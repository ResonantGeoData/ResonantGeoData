var path = require('path');
var webpack = require('webpack');
var vtkRules = require('@kitware/vtk.js/Utilities/config/dependency.js').webpack.core.rules;
var cssRules = require('@kitware/vtk.js/Utilities/config/dependency.js').webpack.css.rules;

var entry = path.join(__dirname, './src/index.js');
const sourcePath = path.join(__dirname, './src');
const outputPath = path.join(__dirname, '../rgd_3d/static/rgd_3d/');

module.exports = {
  entry,
  output: {
    path: outputPath,
    filename: 'vtkjs_viewer.js'
  },
  module: {
    rules: [
      { test: /\.html$/, loader: 'html-loader' },
      { test: /\.(png|jpg)$/, use: 'url-loader' },
      { test: /\.svg$/, use: [{ loader: 'raw-loader' }] }
    ].concat(vtkRules, cssRules)
  },
  resolve: {
    modules: [
      path.resolve(__dirname, 'node_modules'),
      sourcePath
    ]
  }
};
