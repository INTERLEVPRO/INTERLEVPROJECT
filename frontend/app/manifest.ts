import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "INTERLEV AI",
    short_name: "INTERLEV",
    description: "Autonomous recruitment agents for CV formatting, job discovery, and matching.",
    start_url: "/",
    display: "standalone",
    background_color: "#b8b8b6",
    theme_color: "#8c6763",
  };
}
