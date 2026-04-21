import pxtorpx from 'postcss-pxtorpx-pro';
import postcssImport from 'postcss-import';

const config = {
  plugins: [
    postcssImport(),
    pxtorpx({ transform: (x) => x }),
  ],
};

export default config;
