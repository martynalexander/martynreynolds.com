import { defineConfig } from "@stackbit/types";
import { GitContentSource } from "@stackbit/cms-git";

export default defineConfig({
  stackbitVersion: "~0.6.0",
  ssgName: "custom", // Tells the engine this is pure custom HTML
  nodeVersion: "18",
  contentSources: [
    new GitContentSource({
      rootPath: __dirname,
      showDrafts: true,
      collections: [
        {
          name: "page",
          label: "Pages",
          path: "index.html",
          type: "page",
          urlPath: "/",
          fields: [
            {
              name: "title",
              type: "string",
              label: "Site Title",
              required: true
            }
          ]
        }
      ]
    })
  ]
});
