import { defineConfig } from "tinacms";

export default defineConfig({
  branch: "main",
  clientId: null, // Free local/personal build
  token: null,
  build: {
    outputFolder: "admin",
    publicFolder: "./",
  },
  media: {
    tina: {
      mediaRoot: "",
      publicFolder: "./",
    },
  },
  schema: {
    collections: [
      {
        name: "archive",
        label: "Artwork Archive",
        path: "./",
        match: {
          include: "index",
        },
        fields: [
          {
            type: "string",
            name: "title",
            label: "Main Website Title",
          },
        ],
      },
    ],
  },
});
