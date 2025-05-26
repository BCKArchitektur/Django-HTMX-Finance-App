/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../**/templates/**/*.html"],
  theme: {
    extend: {
    },
  },
  plugins: [
    require('daisyui'),
    require('@tailwindcss/line-clamp'),
  ],
  daisyui: {
    themes: ["light"], 
  },
}