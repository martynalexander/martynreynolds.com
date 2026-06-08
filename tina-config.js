import { defineConfig } from "tinacms";

export default defineConfig({
  branch: "main",
  clientId: "1524d320-7ee4-4a3e-bca7-351916403e51", // Your exact Client ID
  token: null, // Left blank for personal deployment
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
        name: "portfolio",
        label: "Artwork Archive",
        path: "./",
        match: {
          include: "index",
        },
        ui: {
          router: () => "/",
        },
        fields: [
          {
            type: "object",
            list: true,
            name: "artworks",
            label: "Images & Videos List",
            ui: {
              itemProps: (item) => {
                return { label: item?.title || "New Artwork Entry" };
              },
            },
            fields: [
              {
                type: "image",
                name: "src",
                label: "Upload or Select File",
              },
              {
                type: "string",
                name: "title",
                label: "Artwork Information Line (Use | slashes)",
              },
            ],
          },
        ],
      },
    ],
  },
});
