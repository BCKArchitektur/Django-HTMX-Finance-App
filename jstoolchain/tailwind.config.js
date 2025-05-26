/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../**/templates/**/*.html"],
  theme: {
    extend: {
      fontFamily: {
        neue: ['"Neue Hans Kendrick Regular"', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('daisyui'),
    require('@tailwindcss/line-clamp'),
  ],
}

