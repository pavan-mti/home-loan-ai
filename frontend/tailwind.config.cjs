module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0b1220',
        mist: '#eef2f8',
        sand: '#f4ede4',
        gold: '#b98a3b',
        teal: '#0f7c7d',
        coral: '#d9724b',
      },
      boxShadow: {
        panel: '0 18px 50px rgba(11, 18, 32, 0.14)',
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        body: ['Manrope', 'sans-serif'],
      },
      backgroundImage: {
        'hero-radial': 'radial-gradient(circle at top left, rgba(185, 138, 59, 0.22), transparent 34%), radial-gradient(circle at right top, rgba(15, 124, 125, 0.20), transparent 28%), linear-gradient(180deg, #f8f4ee 0%, #eef2f8 100%)',
      },
    },
  },
  plugins: [],
}