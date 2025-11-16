// postcss.config.mjs
export default {
    plugins: {
        "@tailwindcss/postcss": {}, // NEW required plugin for Tailwind v4
        autoprefixer: {},
    },
};
