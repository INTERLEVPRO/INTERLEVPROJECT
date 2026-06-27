import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://interlev.ai"),
  title: {
    default: "INTERLEV AI | Autonomous Recruitment Agents",
    template: "%s | INTERLEV AI",
  },
  description:
    "INTERLEV AI helps teams automate CV formatting, freelance job discovery, candidate matching, review workflows, and recruitment operations.",
  keywords: [
    "autonomous recruitment agent",
    "AI recruitment automation",
    "CV formatting",
    "freelance job matching",
    "candidate matching software",
    "INTERLEV AI",
  ],
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "INTERLEV AI | Autonomous Recruitment Agents",
    description:
      "Autonomous CV formatting, job discovery, matching, and review workflows for professional recruitment operations.",
    url: "/",
    siteName: "INTERLEV AI",
    type: "website",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "INTERLEV AI",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description:
      "Autonomous recruitment agents for CV formatting, freelance job search, candidate matching, and review workflows.",
    url: process.env.NEXT_PUBLIC_SITE_URL || "https://interlev.ai",
    publisher: {
      "@type": "Organization",
      name: "INTERLEV",
      url: process.env.NEXT_PUBLIC_SITE_URL || "https://interlev.ai",
    },
  };

  return (
    <html lang="en">
      <body className={inter.className}>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        {children}
      </body>
    </html>
  );
}
