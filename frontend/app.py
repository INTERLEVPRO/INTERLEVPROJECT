import html
import hashlib
import json
import os
import re
import time
from io import BytesIO
from textwrap import dedent
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", BACKEND_URL).rstrip("/")

st.set_page_config(
    page_title="INTERLEV AI | Autonomous Recruitment",
    layout="wide",
    page_icon=":briefcase:",
    initial_sidebar_state="expanded",
)


def render_html(markup: str) -> None:
    st.html(dedent(markup).strip())


render_html(
    """
    <style>
    :root {
        --app-bg: #b8b8b6;
        --surface: #f3f3f0;
        --surface-soft: #e8e8e5;
        --ink: #1f1f1d;
        --muted: #6c6a66;
        --line: #d1cfca;
        --brand: #8c6763;
        --brand-soft: #efe2df;
        --green: #5f7a68;
        --green-soft: #e4ece5;
        --amber: #a5642d;
        --amber-soft: #f1e3d5;
        --red: #9d5752;
        --red-soft: #f2e1df;
        --sky: #7f7068;
        --sky-soft: #e7e2de;
    }

    .stApp {
        background: var(--app-bg);
        color: var(--ink);
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
        max-width: 1260px;
    }

    section[data-testid="stSidebar"] {
        background: #efefed;
        border-right: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--muted);
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 18px;
        margin-bottom: 0;
    }

    section[data-testid="stSidebar"] [role="radiogroup"] label {
        min-height: 34px;
        padding: 5px 8px;
        border-radius: 8px;
        color: var(--ink);
        font-weight: 650;
    }

    section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: var(--brand-soft);
    }

    h1, h2, h3, p, span, label {
        letter-spacing: 0;
    }

    h1 {
        font-size: 30px;
        line-height: 1.2;
        margin-bottom: 0.25rem;
    }

    h2 {
        font-size: 21px;
    }

    h3 {
        font-size: 17px;
    }

    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 20px;
        padding: 18px 20px;
        margin-bottom: 18px;
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 8px 24px rgba(20, 33, 61, 0.05);
    }

    .app-header p {
        margin: 7px 0 0 0;
        color: var(--muted);
        line-height: 1.45;
        max-width: 760px;
    }

    .header-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .status-pill,
    .pill {
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 4px 10px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: var(--surface-soft);
        color: var(--muted);
        font-size: 12px;
        font-weight: 650;
        white-space: nowrap;
    }

    .pill-blue {
        background: var(--brand-soft);
        border-color: #d7c4c0;
        color: var(--brand);
    }

    .pill-green {
        background: var(--green-soft);
        border-color: #b7e3d5;
        color: var(--green);
    }

    .pill-amber {
        background: var(--amber-soft);
        border-color: #fde68a;
        color: var(--amber);
    }

    .pill-red {
        background: var(--red-soft);
        border-color: #fecaca;
        color: var(--red);
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 16px;
    }

    .kpi-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 16px;
        min-height: 92px;
    }

    .kpi-card .value {
        font-size: 30px;
        line-height: 1;
        font-weight: 780;
        color: var(--ink);
        margin-bottom: 8px;
    }

    .kpi-card .label {
        color: var(--muted);
        font-size: 13px;
        font-weight: 620;
    }

    .section-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
    }

    .section-card h3 {
        margin-top: 0;
    }

    .action-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 16px;
    }

    .action-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 16px;
        min-height: 116px;
    }

    .action-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background: var(--sky-soft);
        color: var(--sky);
        font-size: 18px;
        margin-bottom: 9px;
    }

    .action-card .eyebrow {
        font-size: 12px;
        color: var(--muted);
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .action-card strong {
        display: block;
        font-size: 16px;
        color: var(--ink);
        margin-bottom: 7px;
    }

    .action-card span {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.45;
    }

    .agent-row {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 12px;
        align-items: center;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        padding: 13px 14px;
        margin-bottom: 10px;
    }

    .agent-row strong {
        display: block;
        margin-bottom: 3px;
    }

    .agent-row span {
        color: var(--muted);
        font-size: 13px;
    }

    .source-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
    }

    .source-item {
        background: var(--surface-soft);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 10px;
        min-height: 58px;
    }

    .source-item strong {
        display: block;
        font-size: 13px;
        margin-bottom: 3px;
    }

    .source-item span {
        color: var(--muted);
        font-size: 12px;
    }

    .empty-state {
        background: var(--surface);
        border: 1px dashed #b7c5d7;
        border-radius: 8px;
        padding: 22px;
        color: var(--muted);
        text-align: center;
    }

    .timeline {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 10px;
        margin-top: 8px;
    }

    .timeline-step {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 12px;
        min-height: 98px;
    }

    .timeline-step .step-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        font-size: 12px;
        font-weight: 800;
        background: var(--surface-soft);
        border: 1px solid var(--line);
        color: var(--muted);
        margin-bottom: 8px;
    }

    .timeline-step.success .step-icon {
        background: var(--green-soft);
        border-color: #b7e3d5;
        color: var(--green);
    }

    .timeline-step.running .step-icon {
        background: var(--brand-soft);
        border-color: #d7c4c0;
        color: var(--brand);
    }

    .timeline-step.error .step-icon {
        background: var(--red-soft);
        border-color: #fecaca;
        color: var(--red);
    }

    .timeline-step.warning .step-icon {
        background: var(--amber-soft);
        border-color: #fde68a;
        color: var(--amber);
    }

    .timeline-step strong {
        display: block;
        font-size: 13px;
        margin-bottom: 4px;
    }

    .timeline-step span {
        color: var(--muted);
        font-size: 12px;
    }

    .notification-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        padding: 12px;
        margin-bottom: 10px;
    }

    .notification-card.unread {
        border-color: #d7c4c0;
        background: #f7f3f1;
    }

    .notification-card strong {
        display: block;
        margin-bottom: 4px;
    }

    .notification-card p {
        margin: 0 0 8px 0;
        color: var(--muted);
        font-size: 13px;
    }

    .match-card-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-top: 10px;
    }

    .match-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        padding: 14px;
        min-height: 162px;
    }

    .match-card-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
        margin-bottom: 8px;
    }

    .match-card strong {
        display: block;
        color: var(--ink);
        font-size: 15px;
        line-height: 1.35;
    }

    .match-score {
        color: var(--green);
        font-size: 22px;
        font-weight: 800;
        white-space: nowrap;
    }

    .match-card p {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.45;
        margin: 8px 0;
    }

    .match-card .meta-line {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.45;
        margin: 8px 0;
    }

    .match-card .inline-label {
        display: inline;
        color: var(--ink);
    }

    .match-card a {
        color: var(--brand);
        font-size: 13px;
        font-weight: 700;
        text-decoration: none;
    }

    .cv-preview-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        padding: 14px;
        margin: 10px 0;
    }

    .cv-preview-card h4 {
        margin: 0 0 8px 0;
        font-size: 14px;
        color: var(--ink);
    }

    .cv-preview-card p {
        margin: 0;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.5;
    }

    .stButton > button {
        border-radius: 6px;
        min-height: 42px;
        border: 1px solid var(--brand);
        background: var(--brand);
        color: white;
        font-weight: 720;
    }

    .stButton > button:hover,
    .stButton > button:focus {
        background: #765652;
        border-color: #765652;
        color: #ffffff;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 8px 14px;
    }

    .stDataFrame {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
    }

    @media (max-width: 980px) {
        .kpi-grid,
        .action-strip,
        .source-grid,
        .timeline,
        .match-card-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .app-header {
            flex-direction: column;
        }

        .header-actions {
            justify-content: flex-start;
        }
    }

    @media (max-width: 620px) {
        .kpi-grid,
        .action-strip,
        .source-grid,
        .timeline,
        .match-card-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """
)

render_html(
    """
    <style>
    :root {
        --app-bg: #070911;
        --surface: rgba(17, 20, 34, 0.86);
        --surface-soft: rgba(26, 31, 52, 0.88);
        --ink: #f4f7ff;
        --muted: #aab4cf;
        --line: rgba(125, 151, 255, 0.26);
        --brand: #37b8ff;
        --brand-soft: rgba(55, 184, 255, 0.13);
        --violet: #8b5cff;
        --pink: #ff4fd8;
        --green: #38f2c2;
        --green-soft: rgba(56, 242, 194, 0.12);
        --amber: #ffc857;
        --amber-soft: rgba(255, 200, 87, 0.12);
        --red: #ff6b7a;
        --red-soft: rgba(255, 107, 122, 0.12);
        --sky: #50e7ff;
        --sky-soft: rgba(80, 231, 255, 0.12);
    }

    .stApp {
        background:
            linear-gradient(90deg, #07080d 0%, #10142b 4%, #242d59 18%, #31376b 32%, #111420 50%, #31376b 68%, #242d59 82%, #10142b 96%, #07080d 100%);
        color: var(--ink);
    }

    .block-container {
        max-width: 1320px;
        padding-top: 1rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #080a12 0%, #111327 100%);
        border-right: 1px solid rgba(130, 157, 255, 0.22);
        box-shadow: 18px 0 50px rgba(0, 0, 0, 0.28);
    }

    section[data-testid="stSidebar"] h1 {
        color: #f4f7ff;
        font-weight: 800;
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--muted);
    }

    section[data-testid="stSidebar"] [role="radiogroup"] label {
        color: #cbd5ff;
        border: 1px solid transparent;
        background: transparent;
    }

    section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(55, 184, 255, 0.12);
        border-color: rgba(55, 184, 255, 0.32);
    }

    h1, h2, h3, p, span, label {
        letter-spacing: 0;
    }

    h1, h2, h3 {
        color: var(--ink);
    }

    .app-header {
        position: relative;
        overflow: hidden;
        align-items: center;
        min-height: 292px;
        padding: 34px 38px;
        background:
            linear-gradient(135deg, rgba(10, 13, 24, 0.96) 0%, rgba(17, 20, 38, 0.94) 54%, rgba(50, 30, 83, 0.74) 100%);
        border: 1px solid rgba(124, 157, 255, 0.34);
        border-radius: 8px;
        box-shadow: 0 28px 80px rgba(0, 0, 0, 0.42), inset 0 0 90px rgba(88, 116, 255, 0.10);
    }

    .app-header::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(105deg, transparent 0 59%, rgba(255, 79, 216, 0.68) 60%, transparent 61%),
            linear-gradient(105deg, transparent 0 63%, rgba(55, 184, 255, 0.55) 64%, transparent 65%);
        opacity: 0.72;
        pointer-events: none;
    }

    .app-header > div {
        position: relative;
        z-index: 1;
    }

    .app-header h1 {
        font-size: 42px;
        line-height: 1.08;
        margin: 0;
        max-width: 620px;
    }

    .gradient-word {
        background: linear-gradient(90deg, #36c4ff, #8b5cff, #ff4fd8);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }

    .app-header p {
        color: #b9c4de;
        max-width: 610px;
        font-size: 15px;
        line-height: 1.6;
        margin-top: 16px;
    }

    .header-actions {
        align-self: flex-start;
    }

    .pill,
    .status-pill {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(133, 157, 255, 0.26);
        color: #dce5ff;
        backdrop-filter: blur(14px);
    }

    .pill-blue {
        background: linear-gradient(90deg, rgba(55, 184, 255, 0.22), rgba(139, 92, 255, 0.18));
        border-color: rgba(78, 186, 255, 0.52);
        color: #bcecff;
    }

    .pill-green {
        background: rgba(56, 242, 194, 0.14);
        border-color: rgba(56, 242, 194, 0.42);
        color: #8dffe4;
    }

    .pill-amber {
        background: rgba(255, 200, 87, 0.14);
        border-color: rgba(255, 200, 87, 0.38);
        color: #ffe0a0;
    }

    .pill-red {
        background: rgba(255, 107, 122, 0.14);
        border-color: rgba(255, 107, 122, 0.42);
        color: #ffb4bd;
    }

    .hero-visual {
        position: relative;
        width: 300px;
        min-width: 260px;
        height: 245px;
        perspective: 900px;
    }

    .ai-helmet {
        position: absolute;
        right: 18px;
        top: 16px;
        width: 190px;
        height: 190px;
        transform-style: preserve-3d;
        transform: rotateY(-20deg) rotateX(8deg);
        border-radius: 50% 46% 42% 52%;
        background:
            radial-gradient(circle at 34% 18%, rgba(218, 247, 255, 0.96), transparent 18%),
            radial-gradient(circle at 58% 44%, rgba(55, 184, 255, 0.85), transparent 22%),
            linear-gradient(145deg, #07111e 8%, #111a2b 38%, #345980 62%, #05070c 100%);
        border: 1px solid rgba(180, 226, 255, 0.58);
        box-shadow:
            inset -28px -24px 38px rgba(0, 0, 0, 0.72),
            inset 18px 18px 24px rgba(105, 204, 255, 0.25),
            0 0 34px rgba(55, 184, 255, 0.38),
            0 0 72px rgba(139, 92, 255, 0.32);
    }

    .ai-helmet::before {
        content: "";
        position: absolute;
        right: 28px;
        top: 54px;
        width: 74px;
        height: 74px;
        border-radius: 50%;
        background:
            radial-gradient(circle, #07111e 0 28%, #37b8ff 29% 34%, #0b1020 35% 48%, #9be7ff 49% 55%, transparent 56%);
        box-shadow: 0 0 28px rgba(80, 231, 255, 0.64), inset 0 0 18px rgba(0, 0, 0, 0.72);
    }

    .ai-helmet::after {
        content: "";
        position: absolute;
        left: 46px;
        bottom: -52px;
        width: 102px;
        height: 70px;
        border-radius: 18px 18px 40px 40px;
        background: linear-gradient(180deg, #142037, #05070c);
        border: 1px solid rgba(114, 168, 255, 0.42);
        transform: skewX(-10deg);
        box-shadow: inset 0 0 24px rgba(55, 184, 255, 0.22);
    }

    .helmet-line {
        position: absolute;
        right: 4px;
        top: 16px;
        width: 210px;
        height: 210px;
        border-radius: 50%;
        border: 2px solid rgba(255, 79, 216, 0.52);
        transform: rotateZ(25deg) rotateX(64deg);
        filter: drop-shadow(0 0 16px rgba(255, 79, 216, 0.9));
    }

    .circuit-rail {
        position: absolute;
        right: 68px;
        bottom: 16px;
        width: 170px;
        height: 48px;
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        transform: rotateX(56deg) rotateZ(-6deg);
    }

    .circuit-rail span {
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(190, 204, 255, 0.22);
        box-shadow: inset 0 0 16px rgba(55, 184, 255, 0.15), 0 10px 22px rgba(0, 0, 0, 0.38);
    }

    .kpi-card,
    .section-card,
    .action-card,
    .agent-row,
    .source-item,
    .timeline-step,
    .notification-card,
    .match-card,
    .cv-preview-card {
        background: linear-gradient(180deg, rgba(20, 23, 39, 0.92), rgba(10, 12, 22, 0.88));
        border-color: rgba(125, 151, 255, 0.26);
        color: var(--ink);
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.26);
    }

    .kpi-card .value,
    .action-card strong,
    .agent-row strong,
    .source-item strong,
    .timeline-step strong,
    .notification-card strong,
    .match-card strong,
    .match-card .inline-label,
    .cv-preview-card h4 {
        color: #f4f7ff;
    }

    .kpi-card .label,
    .action-card span,
    .agent-row span,
    .source-item span,
    .timeline-step span,
    .notification-card p,
    .match-card p,
    .match-card .meta-line,
    .cv-preview-card p {
        color: var(--muted);
    }

    .match-score {
        color: #38f2c2;
        text-shadow: 0 0 18px rgba(56, 242, 194, 0.44);
    }

    .stButton > button {
        border: 1px solid rgba(94, 205, 255, 0.52);
        background: linear-gradient(90deg, #27b7ff, #8b5cff 58%, #ff4fd8);
        color: white;
        box-shadow: 0 12px 32px rgba(88, 92, 255, 0.28);
    }

    .stButton > button:hover,
    .stButton > button:focus {
        border-color: rgba(255, 255, 255, 0.68);
        background: linear-gradient(90deg, #4bd0ff, #9b72ff 58%, #ff74df);
        color: white;
    }

    [data-testid="stFileUploader"],
    [data-testid="stTextInput"],
    [data-testid="stTextArea"],
    [data-testid="stRadio"] {
        color: var(--ink);
    }

    .stTextInput input,
    .stTextArea textarea {
        background: rgba(8, 11, 22, 0.78);
        color: #f4f7ff;
        border-color: rgba(125, 151, 255, 0.32);
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(125, 151, 255, 0.26);
        color: #dce5ff;
    }

    .stDataFrame {
        border-color: rgba(125, 151, 255, 0.26);
    }

    .empty-state {
        background: rgba(8, 11, 22, 0.74);
        border-color: rgba(125, 151, 255, 0.30);
        color: var(--muted);
    }

    .feature-panel {
        display: grid;
        gap: 12px;
    }

    .feature-panel .feature {
        min-height: 96px;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid rgba(125, 151, 255, 0.26);
        background: linear-gradient(135deg, rgba(23, 27, 48, 0.92), rgba(9, 11, 21, 0.90));
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.24);
    }

    .feature strong {
        display: block;
        color: #f4f7ff;
        margin-bottom: 7px;
        font-size: 15px;
    }

    .feature span {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.45;
    }

    .sidebar-brand {
        display: grid;
        gap: 4px;
        padding: 14px 12px;
        margin-bottom: 10px;
        border: 1px solid rgba(94, 205, 255, 0.26);
        border-radius: 8px;
        background:
            radial-gradient(circle at 16% 18%, rgba(55, 184, 255, 0.22), transparent 34%),
            linear-gradient(135deg, rgba(16, 20, 38, 0.94), rgba(8, 10, 18, 0.94));
        box-shadow: inset 0 0 30px rgba(139, 92, 255, 0.10);
    }

    .sidebar-brand strong {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #f4f7ff;
        font-size: 15px;
        letter-spacing: 0;
    }

    .sidebar-brand strong::before {
        content: "";
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: linear-gradient(135deg, #37b8ff, #8b5cff);
        box-shadow: 0 0 16px rgba(55, 184, 255, 0.86);
    }

    .sidebar-brand span {
        color: var(--muted);
        font-size: 12px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(125, 151, 255, 0.30);
        background:
            linear-gradient(180deg, rgba(16, 19, 34, 0.94), rgba(8, 10, 18, 0.92));
        box-shadow: 0 22px 48px rgba(0, 0, 0, 0.30), inset 0 0 48px rgba(55, 184, 255, 0.06);
    }

    [data-testid="stFileUploaderDropzone"] {
        background: rgba(8, 11, 22, 0.76);
        border: 1px dashed rgba(80, 231, 255, 0.42);
        border-radius: 8px;
    }

    [data-testid="stFileUploaderDropzone"] button {
        border-color: rgba(94, 205, 255, 0.46);
        background: rgba(55, 184, 255, 0.14);
        color: #dff7ff;
    }

    div[data-baseweb="radio"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(125, 151, 255, 0.20);
        border-radius: 8px;
        padding: 8px 10px;
    }

    .stAlert {
        border-radius: 8px;
    }

    div[data-testid="stWidgetLabel"],
    div[data-testid="stWidgetLabel"] label,
    div[data-testid="stWidgetLabel"] p,
    div[data-testid="stWidgetLabel"] span,
    [role="radiogroup"] label,
    [role="radiogroup"] label span,
    [data-baseweb="radio"] label,
    [data-baseweb="radio"] label span,
    .stTextInput label,
    .stFileUploader label,
    .stSelectbox label,
    .stCheckbox label {
        color: #eef3ff !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: rgba(238, 243, 255, 0.68) !important;
        opacity: 1 !important;
    }

    .stTextInput input,
    .stTextArea textarea {
        color: #ffffff !important;
        caret-color: #50e7ff;
    }

    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploaderDropzone"] * {
        color: #dfe8ff !important;
    }

    @media (max-width: 980px) {
        .hero-visual {
            width: 100%;
            min-width: 0;
            height: 230px;
        }

        .app-header h1 {
            font-size: 34px;
        }
    }
    </style>
    """
)


def escape(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def labelize(value: Any) -> str:
    raw = str(value or "")
    return raw.replace("_", " ").strip().title() or "Not Set"


def api_get(path: str, fallback: Any = None) -> Any:
    try:
        response = requests.get(f"{BACKEND_URL}{path}", timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception:
        return fallback


def api_put(path: str, payload: Dict[str, Any]) -> tuple[bool, Any]:
    try:
        response = requests.put(f"{BACKEND_URL}{path}", json=payload, timeout=12)
        return response.ok, response.json() if response.content else {}
    except Exception as exc:
        return False, str(exc)


def api_delete(path: str) -> tuple[bool, Any]:
    try:
        response = requests.delete(f"{BACKEND_URL}{path}", timeout=12)
        return response.ok, response.json() if response.content else {}
    except Exception as exc:
        return False, str(exc)


def api_post_file(path: str, file, data: Dict[str, str]) -> tuple[bool, Any]:
    try:
        files = {"file": (file.name, file.getvalue())}
        response = requests.post(f"{BACKEND_URL}{path}", files=files, data=data, timeout=30)
        return response.ok, response.json() if response.content else {}
    except Exception as exc:
        return False, str(exc)


def api_post_json(path: str, payload: Dict[str, Any]) -> tuple[bool, Any]:
    try:
        response = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=30)
        return response.ok, response.json() if response.content else {}
    except Exception as exc:
        return False, str(exc)


def api_get_file(path: str) -> tuple[bool, bytes, str, str]:
    try:
        response = requests.get(f"{BACKEND_URL}{path}", timeout=45)
        response.raise_for_status()
        disposition = response.headers.get("content-disposition", "")
        match = re.search(r'filename="?([^";]+)"?', disposition)
        filename = match.group(1) if match else "INTERLEV_CV.pdf"
        return True, response.content, filename, ""
    except Exception as exc:
        return False, b"", "", str(exc)


def api_post_file_download(path: str, payload: Dict[str, Any]) -> tuple[bool, bytes, str, str]:
    try:
        response = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=45)
        response.raise_for_status()
        disposition = response.headers.get("content-disposition", "")
        match = re.search(r'filename="?([^";]+)"?', disposition)
        filename = match.group(1) if match else "INTERLEV_CV.pdf"
        return True, response.content, filename, ""
    except Exception as exc:
        return False, b"", "", str(exc)


def public_backend_url(path: str) -> str:
    return f"{PUBLIC_BACKEND_URL}{path}"


def load_settings() -> Dict[str, Any]:
    return api_get("/api/settings/", {})


def effective_min_match_score(config: Dict[str, Any]) -> int:
    raw_score = config.get("automation", {}).get("min_match_score", 50)
    try:
        return max(50, min(100, int(raw_score)))
    except (TypeError, ValueError):
        return 50


def match_score_value(match: Dict[str, Any]) -> float:
    try:
        return float(match.get("match_percentage") or 0)
    except (TypeError, ValueError):
        return 0.0


def match_meets_min_score(match: Dict[str, Any], config: Dict[str, Any]) -> bool:
    return match_score_value(match) >= effective_min_match_score(config)


def load_health() -> Dict[str, Any]:
    return api_get("/api/settings/health", {})


def load_notifications(unread_only: bool = False) -> List[Dict[str, Any]]:
    suffix = "?unread_only=true" if unread_only else ""
    return api_get(f"/api/notifications/{suffix}", [])


def load_cvs() -> List[Dict[str, Any]]:
    return api_get("/api/cv/", [])


def load_task_status(task_id: str | None) -> Dict[str, Any]:
    if not task_id:
        return {}
    return api_get(f"/api/cv/status/{task_id}", {})


def latest_cv_for_candidate(candidate_id: int | None) -> Dict[str, Any]:
    if not candidate_id:
        return {}
    cvs = [
        cv for cv in load_cvs() or []
        if int(cv.get("candidate_id") or 0) == int(candidate_id)
    ]
    if not cvs:
        return {}
    return sorted(cvs, key=lambda cv: str(cv.get("created_at") or ""), reverse=True)[0]


def load_cv_preview(candidate_id: int, job_id: int) -> Dict[str, Any]:
    return api_get(f"/api/cv/candidate/{candidate_id}/job/{job_id}/preview", {})


def load_cv_file(
    candidate_id: int,
    job_id: int,
    output_format: str,
    edits: Dict[str, Any] | None = None,
) -> tuple[bool, bytes, str, str]:
    selected_format = (output_format or "pdf").lower()
    if edits:
        return api_post_file_download(
            f"/api/cv/candidate/{candidate_id}/job/{job_id}/download-edited?output_format={selected_format}",
            {"content": edits},
        )
    return api_get_file(f"/api/cv/candidate/{candidate_id}/job/{job_id}/download?output_format={selected_format}")


def enabled_sources(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scope = config.get("automation", {}).get("search_scope")
    sources = config.get("job_sources", [])
    if scope == "all_freelance_sources":
        return sources
    return [source for source in sources if source.get("enabled")]


def normalized_host(url: str) -> str:
    try:
        host = urlparse(str(url or "")).hostname or ""
    except ValueError:
        return ""
    host = host.lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def hosts_match(actual_host: str, allowed_host: str) -> bool:
    if not actual_host or not allowed_host:
        return False
    return (
        actual_host == allowed_host
        or actual_host.endswith(f".{allowed_host}")
        or allowed_host.endswith(f".{actual_host}")
    )


def job_matches_enabled_source(job: Dict[str, Any], config: Dict[str, Any]) -> bool:
    sources = enabled_sources(config)
    if not sources:
        return False

    platform = str(job.get("platform") or "").lower()
    company = str(job.get("company") or "").lower()
    job_host = normalized_host(str(job.get("url") or ""))
    allowed_names = set()
    allowed_hosts = set()

    for source in sources:
        label = str(source.get("label") or "").lower()
        key = str(source.get("key") or "").lower()
        if label:
            allowed_names.add(label)
        if key:
            allowed_names.add(key)
        for source_url in str(source.get("url") or "").split(","):
            source_host = normalized_host(source_url.strip())
            if source_host:
                allowed_hosts.add(source_host)

    if platform:
        return platform in allowed_names
    if company and any(company == name or company.startswith(f"{name} ") for name in allowed_names):
        return True
    return any(hosts_match(job_host, allowed_host) for allowed_host in allowed_hosts)


def visible_jobs(jobs: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    if config.get("ai", {}).get("active_provider") == "mock":
        return jobs or []
    visible = []
    for job in jobs or []:
        url = str(job.get("url") or "").lower()
        platform = str(job.get("platform") or "").lower()
        company = str(job.get("company") or "").lower()
        if (
            "example.com" in url
            or platform in {"demo mode", "fast pass"}
            or company.startswith("tech solutions")
        ):
            continue
        if not job_matches_enabled_source(job, config):
            continue
        visible.append(job)
    return visible


def load_counts() -> Dict[str, int]:
    active_config = load_settings()
    candidates = api_get("/api/candidates/", [])
    jobs = visible_jobs(api_get("/api/jobs/", []), active_config)
    visible_job_ids = {job.get("id") for job in jobs or []}
    logs = api_get("/api/agent-logs/", [])
    notifications = load_notifications()
    matches = 0
    for candidate in candidates or []:
        candidate_matches = api_get(f"/api/candidates/{candidate.get('id')}/matches", [])
        matches += len(
            [
                match for match in candidate_matches or []
                if match.get("job_id") in visible_job_ids and match_meets_min_score(match, active_config)
            ]
        )
    return {
        "candidates": len(candidates or []),
        "jobs": len(jobs or []),
        "matches": matches,
        "alerts": len([item for item in notifications or [] if not item.get("is_read")]),
    }


def render_page_header(title: str, subtitle: str, pills: List[tuple[str, str]] | None = None) -> None:
    pill_html = ""
    for text, style in pills or []:
        pill_html += f'<span class="pill {style}">{escape(text)}</span>'
    headline = (
        '<span class="gradient-word">Automate</span> the Edge'
        if title == "Automate the Edge"
        else escape(title)
    )
    render_html(
        f"""
        <div class="app-header">
            <div>
                <h1>{headline}</h1>
                <p>{escape(subtitle)}</p>
            </div>
            <div class="hero-visual" aria-hidden="true">
                <div class="helmet-line"></div>
                <div class="ai-helmet"></div>
                <div class="circuit-rail">
                    <span></span><span></span><span></span><span></span>
                </div>
            </div>
            <div class="header-actions">{pill_html}</div>
        </div>
        """
    )


def render_kpis(items: List[tuple[str, Any]]) -> None:
    cards = ""
    for label, value in items:
        cards += (
            '<div class="kpi-card">'
            f'<div class="value">{escape(value)}</div>'
            f'<div class="label">{escape(label)}</div>'
            "</div>"
        )
    render_html(f'<div class="kpi-grid">{cards}</div>')


def render_empty(message: str) -> None:
    render_html(f'<div class="empty-state">{escape(message)}</div>')


def render_sources(config: Dict[str, Any]) -> None:
    source_cards = ""
    for source in enabled_sources(config):
        auth = "Login" if source.get("auth_required") else "Open"
        source_cards += (
            '<div class="source-item">'
            f'<strong>{escape(source.get("label"))}</strong>'
            f'<span>{escape(auth)} source</span>'
            "</div>"
        )
    if not source_cards:
        render_empty("No job sources are enabled.")
        return
    render_html(f'<div class="source-grid">{source_cards}</div>')


def render_recent_activity(logs: List[Dict[str, Any]], limit: int = 6) -> None:
    if not logs:
        render_empty("No agent activity yet.")
        return

    rows = []
    for log in logs[:limit]:
        rows.append(
            {
                "Agent": log.get("agent_name"),
                "Task": log.get("task_name"),
                "Status": labelize(log.get("status")),
                "Time": log.get("created_at"),
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)


def latest_campaign_time(notifications: List[Dict[str, Any]]) -> str:
    for item in notifications:
        if item.get("title") == "Campaign started":
            return item.get("created_at") or ""
    return ""


def after_time(items: List[Dict[str, Any]], started_at: str) -> List[Dict[str, Any]]:
    if not started_at:
        return items
    return [item for item in items if str(item.get("created_at") or "") >= started_at]


def step_status(logs: List[Dict[str, Any]], agent_names: List[str]) -> str:
    agent_set = set(agent_names)
    related = [log for log in logs if log.get("agent_name") in agent_set]
    if not related:
        return "waiting"
    latest = sorted(related, key=lambda log: str(log.get("created_at") or ""), reverse=True)[0]
    if latest.get("status") == "error":
        return "error"
    if latest.get("status") == "working":
        return "running"
    if latest.get("status") == "success":
        return "success"
    return "waiting"


def notification_status(notifications: List[Dict[str, Any]], category: str, finished_title: str | None = None) -> str:
    related = [item for item in notifications if item.get("category") == category]
    if finished_title:
        related = [item for item in related if item.get("title") == finished_title]
    if not related:
        return "waiting"
    latest = sorted(related, key=lambda item: str(item.get("created_at") or ""), reverse=True)[0]
    level = latest.get("level")
    if level == "error":
        return "error"
    if level == "warning":
        return "warning"
    return "success"


def render_progress_timeline(logs: List[Dict[str, Any]], notifications: List[Dict[str, Any]]) -> None:
    campaign_started_at = latest_campaign_time(notifications)
    scoped_logs = after_time(logs, campaign_started_at)
    scoped_notifications = after_time(notifications, campaign_started_at)
    campaign_error = any(
        item.get("level") == "error"
        and item.get("title") in ("Campaign error", "CV analysis failed")
        for item in scoped_notifications
    )
    cv_status = "error" if campaign_error else step_status(scoped_logs, ["CV Reader"])
    steps = [
        ("CV", "CV Reading", cv_status),
        ("PR", "Profile Created", step_status(scoped_logs, ["Profiler"])),
        ("FM", "CV Formatted", step_status(scoped_logs, ["Formatter"])),
        ("JS", "Searching Websites", notification_status(scoped_notifications, "job_search", "Website search finished")),
        ("MT", "Matching Jobs", notification_status(scoped_notifications, "match", "Matching finished")),
        ("NT", "Notifications", "success" if scoped_notifications else "waiting"),
    ]
    cards = ""
    for icon, title, status in steps:
        cards += (
            f'<div class="timeline-step {escape(status)}">'
            f'<div class="step-icon">{escape(icon)}</div>'
            f'<strong>{escape(title)}</strong>'
            f'<span>{escape(labelize(status))}</span>'
            "</div>"
        )
    render_html(f'<div class="timeline">{cards}</div>')


def render_notifications(notifications: List[Dict[str, Any]], limit: int | None = 5) -> None:
    if not notifications:
        render_empty("No notifications yet.")
        return
    visible_notifications = notifications if limit is None else notifications[:limit]
    for item in visible_notifications:
        unread_class = " unread" if not item.get("is_read") else ""
        level = labelize(item.get("level"))
        render_html(
            f"""
            <div class="notification-card{unread_class}">
                <strong>{escape(item.get("title"))}</strong>
                <p>{escape(item.get("message"))}</p>
                <span class="pill pill-blue">{escape(level)}</span>
                <span class="pill">{escape(item.get("created_at"))}</span>
            </div>
            """
        )


def render_notifications_toggle(
    title: str,
    notifications: List[Dict[str, Any]],
    key: str,
    limit: int | None = None,
) -> None:
    is_open = bool(st.session_state.get(key, False))
    count = len(notifications or [])
    unread_count = len([item for item in notifications or [] if not item.get("is_read")])
    unread_label = f" - {unread_count} unread" if unread_count else ""
    label = f"{'Hide' if is_open else 'Show'} {title} ({count}){unread_label}"

    if st.button(
        label,
        key=f"{key}_button",
        icon=":material/notifications:",
        width="stretch",
    ):
        st.session_state[key] = not is_open
        st.rerun()

    if st.session_state.get(key, False):
        render_notifications(notifications, limit=limit)


def latest_candidate_id_from_notifications(notifications: List[Dict[str, Any]]) -> int | None:
    for item in notifications:
        data = item.get("data") or {}
        candidate_id = data.get("candidate_id")
        if candidate_id:
            try:
                return int(candidate_id)
            except (TypeError, ValueError):
                return None
    return None


def load_match_cards(
    config: Dict[str, Any],
    candidate_id: int | None = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    candidates = api_get("/api/candidates/", [])
    jobs = visible_jobs(api_get("/api/jobs/", []), config)
    job_map = {job.get("id"): job for job in jobs or []}
    candidate_map = {candidate.get("id"): candidate for candidate in candidates or []}
    candidate_ids = [candidate_id] if candidate_id else list(candidate_map.keys())
    rows_by_pair: Dict[tuple[int, int], Dict[str, Any]] = {}
    threshold = effective_min_match_score(config)

    for current_candidate_id in candidate_ids:
        if not current_candidate_id:
            continue
        candidate = candidate_map.get(
            current_candidate_id,
            {"id": current_candidate_id, "name": "Candidate"},
        )
        for match in api_get(f"/api/candidates/{current_candidate_id}/matches", []) or []:
            current_score = match_score_value(match)
            if current_score < threshold:
                continue
            job = job_map.get(match.get("job_id"))
            if not job:
                continue
            pair = (int(current_candidate_id), int(match.get("job_id")))
            row = {
                "candidate": candidate,
                "job": job,
                "match": match,
            }
            existing = rows_by_pair.get(pair)
            existing_score = match_score_value((existing or {}).get("match", {}))
            current_id = int(match.get("id") or 0)
            existing_id = int((existing or {}).get("match", {}).get("id") or 0)
            if not existing or current_score > existing_score or (
                current_score == existing_score and current_id > existing_id
            ):
                rows_by_pair[pair] = row

    return sorted(
        rows_by_pair.values(),
        key=lambda row: match_score_value(row["match"]),
        reverse=True,
    )[:limit]


def match_card_key(row: Dict[str, Any]) -> str:
    candidate_id = row.get("candidate", {}).get("id")
    job_id = row.get("job", {}).get("id")
    match_id = row.get("match", {}).get("id")
    return f"{candidate_id}_{job_id}_{match_id}"


def render_cv_preview_panel(preview: Dict[str, Any]) -> None:
    selected_format = labelize(preview.get("output_format", "pdf"))
    template_name = preview.get("template_name", "INTERLEV Professional")
    template_file = preview.get("template_file_name") or "Default generated format"
    st.caption(f"{template_name} - {template_file} - selected settings format: {selected_format}")
    for section in preview.get("sections", []):
        render_html(
            f"""
            <div class="cv-preview-card">
                <h4>{escape(section.get("title"))}</h4>
                <p>{escape(section.get("body"))}</p>
            </div>
            """
        )


def render_pdf_preview(data: bytes) -> None:
    try:
        import fitz

        document = fitz.open(stream=data, filetype="pdf")
        if document.page_count < 1:
            st.warning("PDF preview page is not available, but download is ready.")
            return

        page = document[0]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
        st.image(pixmap.tobytes("png"), use_container_width=True)
        if document.page_count > 1:
            st.caption(f"Preview showing page 1 of {document.page_count}. Download includes all pages.")
        document.close()
    except Exception as exc:
        st.warning(f"Preview could not be displayed, but download is ready: {exc}")


def render_docx_preview(data: bytes) -> None:
    try:
        from docx import Document
        from docx.document import Document as DocxDocument
        from docx.oxml.table import CT_Tbl
        from docx.oxml.text.paragraph import CT_P
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        document = Document(BytesIO(data))

        def iter_blocks(parent: DocxDocument):
            for child in parent.element.body.iterchildren():
                if isinstance(child, CT_P):
                    yield Paragraph(child, parent)
                elif isinstance(child, CT_Tbl):
                    yield Table(child, parent)

        parts = [
            """
            <div class="cv-preview-card">
                <div style="font-size:12px;color:var(--muted);margin-bottom:12px;">Final DOCX preview from the selected Settings template</div>
            """
        ]
        for block in iter_blocks(document):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if not text:
                    continue
                style_name = getattr(block.style, "name", "") or ""
                if style_name.lower().startswith("heading") or (text.isupper() and len(text) < 90):
                    parts.append(f"<h4>{escape(text)}</h4>")
                elif text.startswith(("•", "-", "*")):
                    parts.append(f"<p style='margin:4px 0 4px 14px;'>{escape(text)}</p>")
                else:
                    parts.append(f"<p>{escape(text)}</p>")
            else:
                parts.append("<table style='width:100%;border-collapse:collapse;margin:10px 0 18px;'>")
                for row in block.rows:
                    parts.append("<tr>")
                    for cell in row.cells:
                        cell_text = "<br>".join(
                            escape(line)
                            for line in cell.text.splitlines()
                            if line.strip()
                        )
                        parts.append(
                            "<td style='border:1px solid var(--line);padding:8px;vertical-align:top;'>"
                            f"{cell_text or '&nbsp;'}</td>"
                        )
                    parts.append("</tr>")
                parts.append("</table>")
        parts.append("</div>")
        render_html("".join(parts))
    except Exception as exc:
        st.warning(f"DOCX preview could not be displayed, but download is ready: {exc}")


def cv_edit_defaults(preview: Dict[str, Any], candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, str]:
    section_map = {
        str(section.get("title") or "").lower(): str(section.get("body") or "")
        for section in preview.get("sections", [])
    }
    role = section_map.get("role") or job.get("title") or candidate.get("main_role") or ""
    skills = section_map.get("key skills") or ""
    target = section_map.get("target opportunity") or (
        f"{job.get('title') or 'Job'} at {job.get('company') or job.get('platform') or 'client'}"
    )
    return {
        "name": str(section_map.get("name") or candidate.get("name") or ""),
        "role": str(role),
        "phone": str(candidate.get("phone") or ""),
        "email": str(candidate.get("email") or ""),
        "location": str(candidate.get("location") or ""),
        "summary": str(section_map.get("professional summary") or candidate.get("summary") or ""),
        "skills": str(skills),
        "tools": str(skills),
        "languages": "English",
        "certifications": "Available upon request",
        "target_job": str(job.get("title") or role),
        "target_opportunity": str(target),
        "work_experience": (
            f"{role}\n"
            f"{candidate.get('location') or job.get('location') or 'Remote'}\n"
            "Relevant experience tailored for the target role.\n"
            f"{skills or 'N/A'}"
        ),
        "education": "Available upon request",
        "projects": (
            f"{job.get('title') or role}\n"
            f"Prepared for {job.get('title') or role}. Required skills: {', '.join(job.get('required_skills') or []) or 'Not listed'}."
        ),
        "references": "Available upon request.",
    }


def edit_digest(edits: Dict[str, Any]) -> str:
    payload = json.dumps(edits or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()[:10]


def render_cv_edit_form(card_key: str, defaults: Dict[str, str]) -> Dict[str, str]:
    edit_key = f"cv_edits_{card_key}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = defaults

    current_edits = dict(st.session_state.get(edit_key) or defaults)
    with st.expander("Edit CV content", expanded=False):
        with st.form(f"edit_cv_form_{card_key}"):
            left, right = st.columns(2)
            with left:
                name = st.text_input("Name", value=current_edits.get("name", ""))
                role = st.text_input("Role", value=current_edits.get("role", ""))
                phone = st.text_input("Phone", value=current_edits.get("phone", ""))
                email = st.text_input("Email", value=current_edits.get("email", ""))
                location = st.text_input("Location", value=current_edits.get("location", ""))
                skills = st.text_area("Skills", value=current_edits.get("skills", ""), height=90)
                tools = st.text_area("Tools", value=current_edits.get("tools", ""), height=80)
            with right:
                summary = st.text_area("Professional summary", value=current_edits.get("summary", ""), height=118)
                work_experience = st.text_area(
                    "Work experience",
                    value=current_edits.get("work_experience", ""),
                    height=118,
                )
                education = st.text_area("Education", value=current_edits.get("education", ""), height=70)
                projects = st.text_area("Projects", value=current_edits.get("projects", ""), height=82)
                references = st.text_input("References", value=current_edits.get("references", ""))
                languages = st.text_input("Languages", value=current_edits.get("languages", "English"))
                certifications = st.text_input(
                    "Certifications",
                    value=current_edits.get("certifications", "Available upon request"),
                )

            submitted = st.form_submit_button("Apply edits", icon=":material/check:", width="stretch")
            if submitted:
                st.session_state[edit_key] = {
                    "name": name,
                    "role": role,
                    "phone": phone,
                    "email": email,
                    "location": location,
                    "summary": summary,
                    "skills": skills,
                    "tools": tools,
                    "languages": languages,
                    "certifications": certifications,
                    "target_job": current_edits.get("target_job", role),
                    "target_opportunity": current_edits.get("target_opportunity", ""),
                    "work_experience": work_experience,
                    "education": education,
                    "projects": projects,
                    "references": references,
                }
                st.rerun()

    return dict(st.session_state.get(edit_key) or defaults)


@st.dialog("Matched job actions", width="large")
def render_match_actions_popup(row: Dict[str, Any], current_config: Dict[str, Any]) -> None:
    candidate = row["candidate"]
    job = row["job"]
    match = row["match"]
    candidate_id = int(candidate.get("id") or match.get("candidate_id") or 0)
    job_id = int(job.get("id") or match.get("job_id") or 0)
    card_key = match_card_key(row)
    url = job.get("url") or ""

    st.markdown(f"### {job.get('title') or 'Matched Job'}")
    st.caption(f"{job.get('company') or job.get('platform') or 'Client'} - {match.get('match_percentage', 0)}% match")
    st.write(match.get("reason") or "No match reason saved yet.")

    see_col, change_col = st.columns(2)
    with see_col:
        if url:
            st.link_button("See Job", url, icon=":material/open_in_new:", width="stretch")
        else:
            st.button("See Job", disabled=True, width="stretch")
    with change_col:
        if st.button("Change CV", icon=":material/edit_document:", width="stretch", key=f"change_cv_{card_key}"):
            st.session_state[f"show_cv_{card_key}"] = True

    if st.session_state.get(f"show_cv_{card_key}"):
        if not candidate_id or not job_id:
            st.error("Candidate or job ID is missing for this match. Please refresh the page and open the card again.")
            return

        preview = load_cv_preview(candidate_id, job_id)
        selected_output_format = str(
            (preview or {}).get("output_format")
            or current_config.get("cv_format", {}).get("output_format")
            or "pdf"
        ).lower()
        if selected_output_format not in {"docx", "pdf"}:
            selected_output_format = "pdf"
        edit_defaults = cv_edit_defaults(preview or {}, candidate, job)
        current_edits = render_cv_edit_form(card_key, edit_defaults)
        current_digest = edit_digest(current_edits)
        cv_cache_key = (
            f"cv_file_{candidate_id}_{job_id}_"
            f"{(preview or {}).get('template_name', 'cv')}_"
            f"{(preview or {}).get('template_file_name', 'default')}_"
            f"{selected_output_format}_"
            f"{current_digest}"
        )
        if cv_cache_key not in st.session_state:
            with st.spinner(f"Preparing updated CV {selected_output_format.upper()}..."):
                st.session_state[cv_cache_key] = load_cv_file(
                    candidate_id,
                    job_id,
                    selected_output_format,
                    current_edits,
                )

        ok, data, filename, error = st.session_state[cv_cache_key]
        if ok:
            if preview:
                selected_format = labelize(preview.get("output_format", "pdf"))
                template_name = preview.get("template_name", "INTERLEV Professional")
                template_file = preview.get("template_file_name") or "Default generated format"
                st.caption(f"{template_name} - {template_file} - selected settings format: {selected_format}")
            if selected_output_format == "pdf":
                render_pdf_preview(data)
            else:
                render_docx_preview(data)
            st.download_button(
                f"Download {selected_output_format.upper()}",
                data=data,
                file_name=filename,
                mime=(
                    "application/pdf"
                    if selected_output_format == "pdf"
                    else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ),
                icon=":material/download:",
                width="stretch",
                key=f"download_cv_{selected_output_format}_{card_key}",
            )
        else:
            if preview:
                render_cv_preview_panel(preview)
            st.error(f"Could not prepare CV: {error}")

    if st.button("Close", width="stretch", key=f"close_match_{card_key}"):
        st.session_state.pop("selected_match_card", None)
        st.session_state.pop(f"show_cv_{card_key}", None)
        st.rerun()


def render_match_cards(
    rows: List[Dict[str, Any]],
    empty_message: str,
    current_config: Dict[str, Any] | None = None,
) -> None:
    if not rows:
        render_empty(empty_message)
        return

    active_config = current_config or config
    for start in range(0, len(rows), 2):
        columns = st.columns(2)
        for column, row in zip(columns, rows[start:start + 2]):
            with column:
                candidate = row["candidate"]
                job = row["job"]
                match = row["match"]
                matched_skills = ", ".join(match.get("matched_skills") or []) or "No skill tags yet"
                score = match.get("match_percentage", 0)
                card_key = match_card_key(row)
                with st.container(border=True):
                    render_html(
                        f"""
                        <div class="match-card-head">
                            <div>
                                <strong>{escape(job.get("title"))}</strong>
                                <span class="pill">{escape(job.get("platform") or job.get("company"))}</span>
                            </div>
                            <div class="match-score">{escape(score)}%</div>
                        </div>
                        <span class="pill pill-green">{escape(match.get("match_level"))}</span>
                        <span class="pill pill-blue">{escape(candidate.get("name", "Candidate"))}</span>
                        <div class="meta-line"><strong class="inline-label">Assigned Agent:</strong> Matching Agent</div>
                        <div class="meta-line"><strong class="inline-label">Work:</strong> Score fit and tailor CV for this job</div>
                        <p>{escape(match.get("reason"))}</p>
                        <div class="meta-line"><strong class="inline-label">Matched:</strong> {escape(matched_skills)}</div>
                        """
                    )
                    if st.button(
                        "Open matched job card",
                        key=f"open_match_{card_key}",
                        icon=":material/call_made:",
                        width="stretch",
                    ):
                        st.session_state["selected_match_card"] = card_key
                        st.rerun()

    selected_key = st.session_state.get("selected_match_card")
    selected_row = next((row for row in rows if match_card_key(row) == selected_key), None)
    if selected_row:
        render_match_actions_popup(selected_row, active_config)


def source_payload_from_form(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    updated_sources = []
    for source in config.get("job_sources", []):
        updated = dict(source)
        enabled_col, url_col = st.columns([0.32, 0.68])
        with enabled_col:
            updated["enabled"] = st.checkbox(
                source["label"],
                value=bool(source.get("enabled")),
                key=f"source_{source['key']}",
            )
        with url_col:
            updated["url"] = st.text_input(
                f"{source['label']} URL",
                value=source.get("url", ""),
                key=f"url_{source['key']}",
                label_visibility="collapsed",
            )
        updated_sources.append(updated)
    return updated_sources


def connector_payload_from_form(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    updated_connectors = []
    for connector in config.get("mcp_connectors", []):
        updated = dict(connector)
        updated["enabled"] = st.checkbox(
            f"{connector['label']} - {connector.get('purpose', '')}",
            value=bool(connector.get("enabled")),
            key=f"mcp_{connector['key']}",
        )
        updated_connectors.append(updated)
    return updated_connectors


def render_cv_template_manager(cv_config: Dict[str, Any]) -> None:
    template_file_name = cv_config.get("template_file_name") or ""
    if not template_file_name:
        st.info("No saved CV format yet. Upload one below and save.")
        return

    st.markdown("#### Saved CV Format")
    with st.container(border=True):
        st.write(f"**{template_file_name}**")
        st.caption(f"Template name: {cv_config.get('template_name', 'INTERLEV Professional')}")

        view_col, edit_col, delete_col = st.columns(3)
        with view_col:
            st.link_button(
                "View",
                public_backend_url("/api/settings/cv-template/view"),
                icon=":material/visibility:",
                width="stretch",
            )
        with edit_col:
            if st.button("Edit / Replace", icon=":material/edit:", width="stretch", key="edit_cv_template_button"):
                st.session_state["edit_cv_template_open"] = not st.session_state.get("edit_cv_template_open", False)
        with delete_col:
            if st.button("Delete", icon=":material/delete:", width="stretch", key="delete_cv_template_button"):
                st.session_state["delete_cv_template_confirm"] = True

        if st.session_state.get("delete_cv_template_confirm"):
            st.warning("Delete the saved CV format from Settings?")
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Yes, delete", width="stretch", key="confirm_delete_cv_template"):
                    ok, result = api_delete("/api/settings/cv-template")
                    if ok:
                        st.session_state.pop("delete_cv_template_confirm", None)
                        st.session_state.pop("edit_cv_template_open", None)
                        st.success("Saved CV format deleted.")
                        st.rerun()
                    else:
                        st.error(f"Could not delete CV format: {result}")
            with cancel_col:
                if st.button("Cancel", width="stretch", key="cancel_delete_cv_template"):
                    st.session_state.pop("delete_cv_template_confirm", None)
                    st.rerun()

        if st.session_state.get("edit_cv_template_open"):
            extension = str(template_file_name).rsplit(".", 1)[-1].lower()
            text_template = extension in {"txt", "md"}
            content_data = api_get("/api/settings/cv-template/content", {}) if text_template else {}
            with st.form("edit_saved_cv_template_form"):
                edited_name = st.text_input(
                    "Template display name",
                    value=cv_config.get("template_name", "INTERLEV Professional"),
                )
                edited_content = None
                if text_template:
                    edited_content = st.text_area(
                        "Template content",
                        value=content_data.get("content", ""),
                        height=220,
                    )
                else:
                    st.info("PDF/DOCX content cannot be edited in the browser. Replace the file or rename it.")
                replacement_template = st.file_uploader(
                    "Replace saved CV format",
                    type=["docx", "pdf", "txt", "md"],
                    key="replace_saved_cv_template",
                )
                if st.form_submit_button("Save Template Edit"):
                    payload: Dict[str, Any] = {"template_name": edited_name}
                    if edited_content is not None:
                        payload["content"] = edited_content
                    ok, result = api_put("/api/settings/cv-template", payload)
                    if ok and replacement_template is not None:
                        ok, result = api_post_file("/api/settings/cv-template", replacement_template, {})
                    if ok:
                        st.success("Saved CV format updated.")
                        st.session_state.pop("edit_cv_template_open", None)
                        st.rerun()
                    else:
                        st.error(f"Could not update CV format: {result}")


def save_config(payload: Dict[str, Any]) -> None:
    ok, result = api_put("/api/settings/", payload)
    if ok:
        st.success("Saved.")
        st.rerun()
    else:
        st.error(f"Could not save settings: {result}")


config = load_settings()
health = load_health()
brand = config.get("branding", {})
automation = config.get("automation", {})
ai_config = config.get("ai", {})
cv_config = config.get("cv_format", {})
match_threshold = effective_min_match_score(config)

NAV_DISPLAY = {
    "Home": "⌂ Home",
    "Run Campaign": "▶ Run Campaign",
    "Results": "▦ Results",
    "Agents": "◎ Agents",
    "Settings": "⚙ Settings",
    "Logs": "▤ Logs",
}


with st.sidebar:
    backend_online = bool(health)
    backend_label = "Ready" if backend_online else "Offline"
    backend_style = "pill-green" if backend_online else "pill-red"
    render_html(
        """
        <div class="sidebar-brand">
            <strong>INTERLEV.AI</strong>
            <span>Autonomous recruitment console</span>
        </div>
        """
    )
    st.divider()
    menu = st.radio(
        "Main menu",
        [
            "Run Campaign",
            "Agents",
            "Settings",
        ],
        format_func=lambda item: item,
        label_visibility="collapsed",
    )
    st.divider()
    render_html(
        f"""
        <span class="pill {backend_style}">{escape(backend_label)}</span>
        <br><br>
        <span class="pill pill-blue">AI: {escape(labelize(ai_config.get("active_provider", "mock")))}</span>
        """
    )


if menu == "Home":
    counts = load_counts()
    notifications = load_notifications()
    render_page_header(
        "Recruitment Dashboard",
        "Upload a CV, let agents search jobs, then review match cards.",
        [
            (f"{health.get('company_name', 'INTERLEV')}", "pill-blue"),
            (labelize(automation.get("autonomy_level")), "pill-green"),
        ],
    )

    render_kpis(
        [
            ("Candidates", counts["candidates"]),
            ("Jobs Found", counts["jobs"]),
            ("Matches", counts["matches"]),
            ("Unread Notes", counts["alerts"]),
        ]
    )

    if ai_config.get("active_provider") == "mock":
        st.warning("Demo Mode is active. Switch AI provider to OpenAI, Gemini, or Auto for real CV analysis and real website search.")
    elif not ai_config.get("openai_api_key_configured") and not ai_config.get("gemini_api_key_configured"):
        st.error("Real AI key needed. Add an OpenAI or Gemini key in Settings.")

    render_html(
        """
        <div class="action-strip">
            <div class="action-card">
                <div class="action-icon">CV</div>
                <div class="eyebrow">Step 1</div>
                <strong>Upload CV</strong>
                <span>The agent reads skills and experience.</span>
            </div>
            <div class="action-card">
                <div class="action-icon">AI</div>
                <div class="eyebrow">Step 2</div>
                <strong>Search Jobs</strong>
                <span>Uses websites saved in Settings.</span>
            </div>
            <div class="action-card">
                <div class="action-icon">%</div>
                <div class="eyebrow">Step 3</div>
                <strong>See Match Cards</strong>
                <span>Each card shows job fit percentage.</span>
            </div>
        </div>
        """
    )

    left, right = st.columns([1.05, 0.95])
    with left:
        render_notifications_toggle("Latest Notifications", notifications, "home_latest_notifications")
    with right:
        st.subheader("Active Job Sources")
        render_sources(config)
        st.subheader("Recent Activity")
        render_recent_activity(api_get("/api/agent-logs/", []), limit=4)


elif menu == "Run Campaign":
    render_page_header(
        "Automate the Edge",
        "Unlock the next era of recruitment intelligence, where agents read, search, match, and move from thought to action.",
        [
            (f"Output: {labelize(cv_config.get('output_format', 'docx'))}", "pill-blue"),
            (f"Min Score: {match_threshold}", "pill-green"),
        ],
    )

    if ai_config.get("active_provider") == "mock":
        st.info("Demo Mode is active. This mode creates sample data intentionally. Select OpenAI, Gemini, or Auto for real search.")
    elif not ai_config.get("openai_api_key_configured") and not ai_config.get("gemini_api_key_configured"):
        st.error("Real AI key needed before CV analysis can run.")

    campaign_left, campaign_right = st.columns([0.62, 0.38])
    with campaign_left:
        with st.container(border=True):
            st.subheader("Candidate CV")
            uploaded_file = st.file_uploader(
                "CV file",
                type=cv_config.get("accepted_uploads", ["pdf", "docx", "txt", "md"]),
            )
            start_disabled = uploaded_file is None
            if st.button("Start Campaign", disabled=start_disabled, width="stretch"):
                if uploaded_file and uploaded_file.name.lower().endswith((".txt", ".md", ".markdown")):
                    st.session_state["uploaded_text_preview"] = uploaded_file.getvalue().decode(
                        "utf-8",
                        errors="replace",
                    )
                else:
                    st.session_state["uploaded_text_preview"] = ""
                ok, result = api_post_file(
                    "/api/cv/run-full-campaign",
                    uploaded_file,
                    {
                        "keywords": "",
                        "source_url": "",
                        "search_mode": "real_search",
                    },
                )
                if ok:
                    st.session_state["campaign_started"] = True
                    st.session_state["latest_task"] = result.get("task_id")
                    st.session_state["campaign_latest_notifications"] = False
                    st.success(f"Campaign started. Task ID: {result.get('task_id')}")
                else:
                    st.error(f"Could not start campaign: {result}")

    with campaign_right:
        render_html(
            """
            <div class="feature-panel">
                <div class="feature">
                    <strong>Text to Match</strong>
                    <span>CV content becomes candidate skills, role signals, and match-ready profile data.</span>
                </div>
                <div class="feature">
                    <strong>Website Sources</strong>
                    <span>Only enabled Settings websites are searched for matching jobs.</span>
                </div>
                <div class="feature">
                    <strong>AI in Action</strong>
                    <span>Reader, formatter, job searcher, matcher, and notifications work as one flow.</span>
                </div>
            </div>
            """
        )

    if st.session_state.get("campaign_started"):
        st.divider()
        st.subheader("Live Progress")
        time.sleep(2)
        live_logs = api_get("/api/agent-logs/", [])
        live_notifications = load_notifications()
        task_status = load_task_status(st.session_state.get("latest_task"))
        if task_status:
            st.caption(
                f"Task status: {labelize(task_status.get('status'))}"
                + (" - worker is processing or queued" if task_status.get("status") == "PENDING" else "")
            )
        render_progress_timeline(live_logs, live_notifications)
        campaign_started_at = latest_campaign_time(live_notifications)
        scoped_notifications = after_time(live_notifications, campaign_started_at)
        candidate_id = latest_candidate_id_from_notifications(scoped_notifications)
        campaign_error = any(
            item.get("level") == "error"
            and item.get("title") in ("Campaign error", "CV analysis failed")
            for item in scoped_notifications
        )
        cv_record = latest_cv_for_candidate(candidate_id)
        parsed_text = cv_record.get("parsed_text") or st.session_state.get("uploaded_text_preview", "")
        if parsed_text:
            st.subheader("Output Text Format")
            st.text_area(
                "Extracted CV text",
                value=parsed_text,
                height=260,
                label_visibility="collapsed",
            )
        st.subheader("Matched Job Cards")
        if candidate_id:
            if st.button("Refresh Matches", icon=":material/refresh:", width="stretch"):
                st.rerun()
            render_match_cards(
                load_match_cards(config, candidate_id=candidate_id),
                f"No matched job cards found at or above {match_threshold}%.",
            )
        elif campaign_error:
            render_empty("Campaign failed during CV analysis. AI provider was switched to Gemini; start the campaign again.")
        else:
            render_empty("Waiting for this uploaded CV to finish profile creation before showing match cards.")
        render_notifications_toggle(
            "Latest Notifications",
            live_notifications,
            "campaign_latest_notifications",
        )


elif menu == "Results":
    render_page_header(
        "Results",
        "Candidates, discovered jobs, and match records in one review area.",
        [(f"Review Score: {match_threshold}+", "pill-green")],
    )

    tab_candidates, tab_jobs, tab_matches = st.tabs(["Candidates", "Jobs", "Matches"])

    with tab_candidates:
        candidates = api_get("/api/candidates/", [])
        if candidates:
            st.dataframe(candidates, width="stretch", hide_index=True)
        else:
            render_empty("No candidates yet.")

    with tab_jobs:
        jobs = visible_jobs(api_get("/api/jobs/", []), config)
        if jobs:
            st.dataframe(jobs, width="stretch", hide_index=True)
        else:
            render_empty("No real jobs discovered yet. Check Notifications for skipped login-only sources or source errors.")

    with tab_matches:
        candidates = api_get("/api/candidates/", [])
        jobs = visible_jobs(api_get("/api/jobs/", []), config)
        job_map = {job.get("id"): job for job in jobs}
        match_rows = []
        for candidate in candidates or []:
            for match in api_get(f"/api/candidates/{candidate.get('id')}/matches", []) or []:
                if not match_meets_min_score(match, config):
                    continue
                job = job_map.get(match.get("job_id"))
                if not job:
                    continue
                match_rows.append(
                    {
                        "Candidate": candidate.get("name"),
                        "Job": job.get("title"),
                        "Company": job.get("company"),
                        "Platform": job.get("platform"),
                        "URL": job.get("url"),
                        "Score %": match.get("match_percentage"),
                        "Level": match.get("match_level"),
                        "Matched Skills": ", ".join(match.get("matched_skills") or []),
                        "Missing Skills": ", ".join(match.get("missing_skills") or []),
                        "Reason": match.get("reason"),
                    }
                )
        if match_rows:
            st.dataframe(match_rows, width="stretch", hide_index=True)
        else:
            render_empty(f"No matched job cards found at or above {match_threshold}%.")


elif menu == "Agents":
    render_page_header(
        "Agent Team",
        "A clear map of each agent, its job, tools, output, and approval point.",
        [("Audit Ready", "pill-green")],
    )
    blueprint = api_get("/api/settings/agent-blueprint", [])
    for item in blueprint:
        status = "Human input: " + str(item.get("human_input", ""))
        render_html(
            f"""
            <div class="agent-row">
                <div>
                    <strong>{escape(item.get("agent"))}</strong>
                    <span>{escape(item.get("purpose"))}</span>
                </div>
                <span class="pill pill-blue">{escape(status)}</span>
            </div>
            """
        )
        with st.expander(f"Details for {item.get('agent')}"):
            st.write(f"Skills: {', '.join(item.get('skills', []))}")
            st.write(f"Tools: {', '.join(item.get('tools', []))}")
            st.write(f"Output: {item.get('output')}")


elif menu == "Settings":
    render_page_header(
        "Settings",
        "Change providers, websites, CV format, and connector options without editing code.",
        [(labelize(ai_config.get("active_provider")), "pill-blue")],
    )

    tab_brand, tab_ai, tab_auto, tab_sources, tab_cv = st.tabs(
        ["Brand", "AI", "Automation", "Websites", "CV and MCP"]
    )

    with tab_brand:
        with st.form("brand_form"):
            company_name = st.text_input("Company name", value=brand.get("company_name", "INTERLEV"))
            company_url = st.text_input("Company URL", value=brand.get("company_url", "https://interlev.ai"))
            site_url = st.text_input("Public site URL", value=brand.get("site_url", "https://interlev.ai"))
            contact_email = st.text_input("Contact email", value=brand.get("contact_email", "hello@interlev.ai"))
            if st.form_submit_button("Save Brand Settings"):
                save_config(
                    {
                        "branding": {
                            "company_name": company_name,
                            "company_url": company_url,
                            "site_url": site_url,
                            "contact_email": contact_email,
                        }
                    }
                )

    with tab_ai:
        with st.form("ai_form"):
            provider_options = ["mock", "auto", "openai", "gemini"]
            provider = st.selectbox(
                "Active provider",
                provider_options,
                index=provider_options.index(ai_config.get("active_provider", "mock")),
                format_func=labelize,
            )
            if provider == "mock":
                st.info("Mock means explicit Demo Mode. It may create sample candidates and jobs.")
            elif not ai_config.get("openai_api_key_configured") and not ai_config.get("gemini_api_key_configured"):
                st.warning("Real AI key needed. Add a key here before running real CV analysis.")
            model_col1, model_col2 = st.columns(2)
            with model_col1:
                openai_model = st.text_input("OpenAI model", value=ai_config.get("openai_model", "gpt-4o"))
                openai_key = st.text_input(
                    "OpenAI API key",
                    value="",
                    type="password",
                    placeholder="Configured" if ai_config.get("openai_api_key_configured") else "Paste key",
                )
            with model_col2:
                gemini_model = st.text_input("Gemini model", value=ai_config.get("gemini_model", "gemini-2.0-flash"))
                gemini_key = st.text_input(
                    "Gemini API key",
                    value="",
                    type="password",
                    placeholder="Configured" if ai_config.get("gemini_api_key_configured") else "Paste key",
                )
            if st.form_submit_button("Save AI Settings"):
                save_config(
                    {
                        "ai": {
                            "active_provider": provider,
                            "openai_model": openai_model,
                            "gemini_model": gemini_model,
                            "openai_api_key": openai_key,
                            "gemini_api_key": gemini_key,
                        }
                    }
                )

    with tab_auto:
        with st.form("automation_form"):
            auto_col1, auto_col2 = st.columns(2)
            with auto_col1:
                autonomy_options = ["review_before_apply", "draft_only", "fully_autonomous"]
                autonomy_level = st.selectbox(
                    "Autonomy",
                    autonomy_options,
                    index=autonomy_options.index(automation.get("autonomy_level", "review_before_apply")),
                    format_func=labelize,
                )
                scope_options = ["selected_sources", "all_freelance_sources"]
                search_scope = st.selectbox(
                    "Search scope",
                    scope_options,
                    index=scope_options.index(automation.get("search_scope", "selected_sources")),
                    format_func=labelize,
                )
            with auto_col2:
                min_match_score = st.slider("Minimum match score", 50, 100, match_threshold)
                max_jobs_per_source = st.number_input(
                    "Max jobs per source",
                    min_value=1,
                    max_value=50,
                    value=int(automation.get("max_jobs_per_source", 5)),
                )
            human_review_required = st.checkbox(
                "Review before apply or send",
                value=bool(automation.get("human_review_required", True)),
            )
            inbox_scan_enabled = st.checkbox(
                "Inbox scan when connector is enabled",
                value=bool(automation.get("inbox_scan_enabled", False)),
            )
            if st.form_submit_button("Save Automation Settings"):
                save_config(
                    {
                        "automation": {
                            "autonomy_level": autonomy_level,
                            "search_scope": search_scope,
                            "min_match_score": min_match_score,
                            "max_jobs_per_source": int(max_jobs_per_source),
                            "human_review_required": human_review_required,
                            "inbox_scan_enabled": inbox_scan_enabled,
                        }
                    }
                )

    with tab_sources:
        with st.form("sources_form"):
            updated_sources = source_payload_from_form(config)
            default_keywords = st.text_input(
                "Default search keywords",
                value=", ".join(config.get("default_keywords", [])),
            )
            if st.form_submit_button("Save Website Settings"):
                save_config(
                    {
                        "job_sources": updated_sources,
                        "default_keywords": [
                            item.strip() for item in default_keywords.split(",") if item.strip()
                        ],
                    }
                )

    with tab_cv:
        render_cv_template_manager(cv_config)

        with st.form("cv_connector_form"):
            cv_col1, cv_col2 = st.columns(2)
            with cv_col1:
                output_format = st.selectbox(
                    "Output format",
                    ["docx", "pdf"],
                    index=["docx", "pdf"].index(cv_config.get("output_format", "docx")),
                    format_func=labelize,
                )
                template_name = st.text_input(
                    "CV template",
                    value=cv_config.get("template_name", "INTERLEV Professional"),
                )
                uploaded_template = st.file_uploader(
                    "Upload CV format/template",
                    type=["docx", "pdf", "txt", "md"],
                    key="new_cv_template_upload",
                    help="Upload your preferred CV format here, then save. DOCX templates can use placeholders like {{NAME}}, {{ROLE}}, {{SUMMARY}}, {{SKILLS}}, {{TARGET_JOB}}.",
                )
            with cv_col2:
                preserve_original = st.checkbox(
                    "Preserve original CV",
                    value=bool(cv_config.get("preserve_original", True)),
                )
                export_to_google_drive = st.checkbox(
                    "Export to Google Drive when connected",
                    value=bool(cv_config.get("export_to_google_drive", False)),
                )
            st.subheader("Connectors")
            updated_connectors = connector_payload_from_form(config)
            if st.form_submit_button("Save CV and Connector Settings"):
                ok, result = api_put(
                    "/api/settings/",
                    {
                        "cv_format": {
                            "accepted_uploads": cv_config.get("accepted_uploads", ["pdf", "docx", "txt", "md"]),
                            "output_format": output_format,
                            "template_name": template_name,
                            "template_file_path": cv_config.get("template_file_path", ""),
                            "template_file_name": cv_config.get("template_file_name", ""),
                            "preserve_original": preserve_original,
                            "export_to_google_drive": export_to_google_drive,
                        },
                        "mcp_connectors": updated_connectors,
                    },
                )
                if ok and uploaded_template is not None:
                    ok, result = api_post_file("/api/settings/cv-template", uploaded_template, {})
                if ok:
                    st.success("CV format settings saved.")
                    st.rerun()
                else:
                    st.error(f"Could not save CV format settings: {result}")


elif menu == "Logs":
    render_page_header(
        "Logs",
        "Agent activity, admin notifications, errors, and workflow events.",
        [("Latest First", "pill-blue")],
    )
    tab_notifications, tab_logs = st.tabs(["Notifications", "Agent Logs"])
    with tab_notifications:
        notifications = load_notifications()
        render_notifications(notifications, limit=30)
    with tab_logs:
        logs = api_get("/api/agent-logs/", [])
        if logs:
            st.dataframe(logs, width="stretch", hide_index=True)
        else:
            render_empty("No logs yet.")
