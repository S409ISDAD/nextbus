import { radixTheme } from "@radix-ui/themes";

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  presets: [radixTheme],
  theme: {
    extend: {},
  },
  plugins: [],
};
