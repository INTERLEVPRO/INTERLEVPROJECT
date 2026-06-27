import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlencode, urljoin, urlparse, urlunparse

import requests
from sqlalchemy.orm import Session

from backend.app.models.candidate import Candidate
from backend.app.models.job import Job
from backend.app.services.app_settings import JobSourceSettings, enabled_job_sources, load_settings

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - runtime dependency guard
    BeautifulSoup = None


FALLBACK_KEYWORDS = ["Python", "FastAPI", "Backend"]
USER_AGENT = "INTERLEV-AI-RecruitmentBot/1.0 (+https://interlev.ai)"


class JobSearchAgent:
    def __init__(self):
        self.last_stats: Dict[str, Any] = {
            "searched_sources": [],
            "skipped_sources": [],
            "errors": [],
            "demo_mode": False,
        }

    def search_jobs(
        self,
        db: Session,
        keywords: List[str],
        platform: str = "",
        candidate_id: Optional[int] = None,
        source_keys: Optional[List[str]] = None,
        source_url: Optional[str] = None,
        search_mode: str = "real_search",
    ) -> List[Job]:
        settings = load_settings()
        clean_keywords = self._clean_keywords(keywords, settings.default_keywords)
        sources = enabled_job_sources(settings)
        requested_source_url = str(source_url or "").strip()
        if requested_source_url:
            if not requested_source_url.startswith(("http://", "https://")):
                raise ValueError("Specific source URL must start with http:// or https://")
            sources = [self._source_scoped_to_settings(requested_source_url, sources)]
        if source_keys:
            selected = {key.lower() for key in source_keys}
            sources = [source for source in sources if source.key.lower() in selected]
        if platform:
            sources = [source for source in sources if source.label == platform or source.key == platform] or sources

        if not sources and (search_mode or "").lower() != "fast_pass":
            raise ValueError("No enabled websites are configured in Settings for this search.")

        self.last_stats = {
            "searched_sources": [],
            "skipped_sources": [],
            "errors": [],
            "demo_mode": settings.ai.active_provider == "mock",
            "fast_pass": (search_mode or "").lower() == "fast_pass",
            "candidate_id": candidate_id,
            "source_url": requested_source_url,
            "configured_sources": [
                {"key": source.key, "label": source.label, "url": source.url}
                for source in sources
            ],
        }

        if (search_mode or "").lower() == "fast_pass":
            return self._save_jobs(db, self._fast_pass_jobs(db, clean_keywords, candidate_id))

        if settings.ai.active_provider == "mock":
            return self._save_jobs(db, self._demo_jobs(clean_keywords))

        job_payloads: List[Dict[str, Any]] = []
        for source in sources:
            if source.auth_required:
                self.last_stats["skipped_sources"].append({
                    "source": source.label,
                    "reason": "Connector/login required",
                })
                continue

            try:
                source_jobs = self._search_source(source, clean_keywords, settings.automation.max_jobs_per_source)
                job_payloads.extend(source_jobs)
                self.last_stats["searched_sources"].append({
                    "source": source.label,
                    "jobs_found": len(source_jobs),
                })
            except Exception as exc:
                self.last_stats["errors"].append({
                    "source": source.label,
                    "error": str(exc),
                })

        return self._save_jobs(db, job_payloads)

    def validate_source_url(self, source_url: Optional[str]) -> Optional[JobSourceSettings]:
        requested_source_url = str(source_url or "").strip()
        if not requested_source_url:
            return None
        if not requested_source_url.startswith(("http://", "https://")):
            raise ValueError("Specific source URL must start with http:// or https://")
        return self._source_scoped_to_settings(
            requested_source_url,
            enabled_job_sources(load_settings()),
        )

    def _search_source(self, source, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        key = source.key.lower()
        if key == "remoteok" and self._source_has_host(source, "remoteok.com"):
            return self._remoteok_jobs(source, keywords, limit)
        if key == "weworkremotely" and self._source_has_host(source, "weworkremotely.com"):
            return self._weworkremotely_jobs(source, keywords, limit)
        return self._generic_html_jobs(source, keywords, limit)

    def _remoteok_jobs(self, source, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        response = self._get("https://remoteok.com/api")
        data = response.json()
        if not isinstance(data, list):
            return []

        jobs = []
        for item in data[1:]:
            if not isinstance(item, dict):
                continue
            text = " ".join([
                str(item.get("position") or ""),
                str(item.get("company") or ""),
                str(item.get("description") or ""),
                " ".join(item.get("tags") or []),
            ])
            if not self._matches_keywords(text, keywords):
                continue
            jobs.append({
                "title": item.get("position") or "Remote role",
                "company": item.get("company") or "Remote OK client",
                "platform": source.label,
                "url": item.get("url") or item.get("apply_url") or "https://remoteok.com",
                "description": item.get("description") or text,
                "required_skills": self._skills_from_text(text, keywords, item.get("tags") or []),
                "nice_to_have_skills": item.get("tags") or [],
                "budget": item.get("salary") or item.get("salary_min") or None,
                "location": item.get("location") or "Remote",
                "contract_type": "Remote",
                "posted_date": self._parse_epoch(item.get("epoch")),
            })
            if len(jobs) >= limit:
                break
        return jobs

    def _weworkremotely_jobs(self, source, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        jobs: List[Dict[str, Any]] = []
        for base_url in self._source_urls(source.url):
            for keyword in keywords:
                url = self._append_query(base_url, {"term": keyword})
                jobs.extend(self._parse_html_jobs(source, url, keywords, limit - len(jobs)))
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
        return jobs[:limit]

    def _generic_html_jobs(self, source, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        jobs: List[Dict[str, Any]] = []
        for url in self._source_urls(source.url):
            jobs.extend(self._parse_html_jobs(source, url, keywords, limit - len(jobs)))
            if len(jobs) >= limit:
                break
        return jobs[:limit]

    def _parse_html_jobs(self, source, url: str, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        if limit <= 0 or not BeautifulSoup:
            return []

        response = self._get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        selectors = [
            "article",
            "li",
            ".job",
            ".job-listing",
            ".job-card",
            ".project",
            "tr",
        ]
        candidates = []
        for selector in selectors:
            candidates.extend(soup.select(selector))
        if not candidates:
            candidates = soup.find_all("a", href=True)

        jobs: List[Dict[str, Any]] = []
        seen_urls = set()
        for node in candidates:
            link = node if getattr(node, "name", "") == "a" else node.find("a", href=True)
            if not link:
                continue
            href = link.get("href")
            if not href or href.startswith("#"):
                continue
            job_url = urljoin(url, href)
            text = " ".join((node.get_text(" ", strip=True) or "").split())
            title = " ".join((link.get_text(" ", strip=True) or text).split())
            if not title or len(title) < 4 or job_url in seen_urls:
                continue
            if not self._matches_keywords(text or title, keywords):
                continue
            seen_urls.add(job_url)
            jobs.append({
                "title": title[:240],
                "company": source.label,
                "platform": source.label,
                "url": job_url,
                "description": text[:4000] or title,
                "required_skills": self._skills_from_text(text or title, keywords),
                "nice_to_have_skills": [],
                "budget": self._extract_budget(text),
                "location": self._extract_location(text),
                "contract_type": "Freelance",
                "posted_date": None,
            })
            if len(jobs) >= limit:
                break
        if not jobs:
            page_job = self._page_as_job(source, url, soup, keywords)
            if page_job:
                jobs.append(page_job)
        return jobs

    def _demo_jobs(self, keywords: List[str]) -> List[Dict[str, Any]]:
        jobs = []
        for i, keyword in enumerate(keywords[:5]):
            support_skill = "FastAPI" if keyword.lower() == "python" else "Python"
            jobs.append({
                "title": f"Demo Senior {keyword} Developer",
                "company": f"Demo Client {i + 1}",
                "platform": "Demo Mode",
                "url": f"https://example.com/demo-job/{i + 1}",
                "description": "Demo Mode job. Switch AI provider away from mock for real website search.",
                "required_skills": [keyword, support_skill],
                "nice_to_have_skills": ["API", "Cloud"],
                "location": "Remote",
                "contract_type": "Remote Freelance",
                "posted_date": datetime.utcnow(),
            })
        return jobs

    def _fast_pass_jobs(
        self,
        db: Session,
        keywords: List[str],
        candidate_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        candidate = None
        candidate_skills: List[str] = []
        if candidate_id:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if candidate and candidate.skills:
                candidate_skills = [skill.skill_name for skill in candidate.skills if skill.skill_name]

        skills = self._dedupe(candidate_skills + keywords)[:8]
        if not skills:
            skills = FALLBACK_KEYWORDS

        role = (candidate.main_role if candidate else None) or self._role_from_skills(skills)
        candidate_label = candidate_id or "latest"
        templates = [
            ("Remote", "Project Delivery"),
            ("Freelance", "Client Implementation"),
            ("Contract", "Support Sprint"),
        ]
        jobs = []
        for index, (contract_type, focus) in enumerate(templates):
            skill_slice = skills[index:index + 3] or skills[:3]
            primary_skill = skill_slice[0]
            jobs.append({
                "title": f"Fast Pass {role} - {primary_skill} {focus}",
                "company": "INTERLEV Fast Pass",
                "platform": "Fast Pass",
                "url": f"https://interlev.local/fast-pass/{candidate_label}/{index + 1}-{quote_plus(primary_skill.lower())}",
                "description": (
                    "Local Fast Pass lead generated from the uploaded CV skills. "
                    f"Focus skills: {', '.join(skill_slice)}. "
                    "Use this to validate matching immediately; run Real Website Search when ready for live leads."
                ),
                "required_skills": skill_slice,
                "nice_to_have_skills": [skill for skill in skills if skill not in skill_slice][:4],
                "budget": "Review rate with client",
                "location": "Remote",
                "contract_type": contract_type,
                "posted_date": datetime.utcnow(),
            })
        self.last_stats["searched_sources"].append({
            "source": "Fast Pass",
            "jobs_found": len(jobs),
        })
        return jobs

    def _save_jobs(self, db: Session, payloads: List[Dict[str, Any]]) -> List[Job]:
        jobs = []
        for job_data in payloads:
            existing = db.query(Job).filter(Job.url == job_data["url"]).first()
            if existing:
                jobs.append(existing)
                continue
            job = Job(**job_data)
            db.add(job)
            jobs.append(job)
        db.commit()
        return jobs

    def _page_as_job(self, source, url: str, soup, keywords: List[str]) -> Dict[str, Any] | None:
        text = " ".join((soup.get_text(" ", strip=True) or "").split())
        if not text or not self._matches_keywords(text, keywords):
            return None
        title_node = soup.find("h1") or soup.find("title")
        title = " ".join((title_node.get_text(" ", strip=True) if title_node else "").split())
        if not title:
            title = f"{source.label} job opportunity"
        return {
            "title": title[:240],
            "company": source.label,
            "platform": source.label,
            "url": url,
            "description": text[:4000],
            "required_skills": self._skills_from_text(text, keywords),
            "nice_to_have_skills": [],
            "budget": self._extract_budget(text),
            "location": self._extract_location(text),
            "contract_type": "Freelance",
            "posted_date": None,
        }

    def _get(self, url: str):
        return requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/html,application/xhtml+xml",
            },
            timeout=8,
        )

    def _clean_keywords(self, keywords: List[str], defaults: List[str]) -> List[str]:
        if isinstance(keywords, str):
            keywords = [keyword.strip() for keyword in keywords.split(",")]
        clean = [keyword.strip() for keyword in (keywords or []) if keyword and keyword.strip()]
        return clean or defaults or FALLBACK_KEYWORDS

    def _source_urls(self, raw_urls: str) -> List[str]:
        return [url.strip() for url in str(raw_urls or "").split(",") if url.strip().startswith("http")]

    def _source_scoped_to_settings(
        self,
        requested_url: str,
        configured_sources: List[JobSourceSettings],
    ) -> JobSourceSettings:
        requested_host = self._normalized_host(requested_url)
        if not requested_host:
            raise ValueError("Specific source URL must be a valid http(s) URL.")

        for source in configured_sources:
            source_urls = self._source_urls(source.url)
            if any(self._hosts_match(requested_host, self._normalized_host(url)) for url in source_urls):
                return JobSourceSettings(
                    key=source.key,
                    label=source.label,
                    url=requested_url,
                    enabled=True,
                    search_mode=source.search_mode,
                    auth_required=source.auth_required,
                    notes=f"Scoped to Settings source: {source.label}",
                )

        allowed = ", ".join(
            f"{source.label} ({source.url})"
            for source in configured_sources
        ) or "none"
        raise ValueError(
            "Specific source URL is not enabled in Settings. "
            f"Enable/add this website in Settings first. Allowed websites: {allowed}"
        )

    def _source_has_host(self, source: JobSourceSettings, expected_host: str) -> bool:
        expected = self._normalized_host(f"https://{expected_host}")
        return any(
            self._hosts_match(self._normalized_host(url), expected)
            for url in self._source_urls(source.url)
        )

    def _normalized_host(self, url: str) -> str:
        try:
            host = urlparse(url).hostname or ""
        except Exception:
            return ""
        host = host.lower().strip(".")
        return host[4:] if host.startswith("www.") else host

    def _hosts_match(self, actual_host: str, allowed_host: str) -> bool:
        if not actual_host or not allowed_host:
            return False
        return (
            actual_host == allowed_host
            or actual_host.endswith(f".{allowed_host}")
            or allowed_host.endswith(f".{actual_host}")
        )

    def _append_query(self, url: str, params: Dict[str, str]) -> str:
        parsed = urlparse(url)
        current_query = parsed.query
        extra_query = urlencode(params)
        query = f"{current_query}&{extra_query}" if current_query else extra_query
        return urlunparse(parsed._replace(query=query))

    def _dedupe(self, values: List[str]) -> List[str]:
        seen = set()
        clean = []
        for value in values:
            normalized = str(value or "").strip()
            key = normalized.lower()
            if normalized and key not in seen:
                clean.append(normalized)
                seen.add(key)
        return clean

    def _role_from_skills(self, skills: List[str]) -> str:
        lowered = " ".join(skill.lower() for skill in skills)
        if any(item in lowered for item in ("html", "css", "react", "javascript", "typescript")):
            return "Frontend Developer"
        if any(item in lowered for item in ("sql", "python", "java", "fastapi", "django")):
            return "Software Developer"
        if any(item in lowered for item in ("support", "customer", "marketing")):
            return "Operations Specialist"
        return "Candidate"

    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        lower = text.lower()
        return any(keyword.lower() in lower for keyword in keywords)

    def _skills_from_text(self, text: str, keywords: List[str], extra: Optional[List[str]] = None) -> List[str]:
        lower = text.lower()
        skills = [keyword for keyword in keywords if keyword.lower() in lower]
        for item in extra or []:
            if isinstance(item, str) and item.lower() in lower and item not in skills:
                skills.append(item)
        return skills[:8] or keywords[:3]

    def _extract_budget(self, text: str) -> str | None:
        markers = ["$", "€", "£", "hour", "daily", "budget", "rate"]
        if not any(marker in text.lower() for marker in markers):
            return None
        return text[:180]

    def _extract_location(self, text: str) -> str:
        lower = text.lower()
        if "remote" in lower:
            return "Remote"
        if "germany" in lower or "deutschland" in lower:
            return "Germany"
        return "Not specified"

    def _parse_epoch(self, value) -> datetime | None:
        try:
            return datetime.utcfromtimestamp(int(value))
        except Exception:
            return None
