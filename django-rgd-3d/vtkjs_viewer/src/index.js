import '@kitware/vtk.js/favicon';

// Load the rendering pieces we want to use (for both WebGL and WebGPU)
import '@kitware/vtk.js/Rendering/Profiles/Geometry';

import { debounce } from '@kitware/vtk.js/macro';
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray';
import vtkScalarBarActor from '@kitware/vtk.js/Rendering/Core/ScalarBarActor';
import vtkColorMaps from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction/ColorMaps';
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
import vtkURLExtract from '@kitware/vtk.js/Common/Core/URLExtract';
import vtkXMLPolyDataReader from '@kitware/vtk.js/IO/XML/XMLPolyDataReader';
import vtkFPSMonitor from '@kitware/vtk.js/Interaction/UI/FPSMonitor';
import Base64 from '@kitware/vtk.js/Common/Core/Base64';

// Force DataAccessHelper to have access to various data source
import '@kitware/vtk.js/IO/Core/DataAccessHelper/HtmlDataAccessHelper';
import '@kitware/vtk.js/IO/Core/DataAccessHelper/JSZipDataAccessHelper';

import {
  ColorMode,
  ScalarMode
} from '@kitware/vtk.js/Rendering/Core/Mapper/Constants';

import style from './GeometryViewer.module.css';
import icon from './favicon-96x96.png';

let background = [0, 0, 0];
let renderWindow;
let renderer;
let scalarBarActor;

global.pipeline = {};

// Process arguments from URL
const userParams = vtkURLExtract.extractURLParameters();

// Background handling
if (userParams.background) {
  background = userParams.background.split(',').map((s) => Number(s));
}
const selectorClass =
  background.length === 3 && background.reduce((a, b) => a + b, 0) < 1.5
    ? style.dark
    : style.light;

// lut
const lutName = userParams.lut || 'erdc_rainbow_bright';

// field
const field = userParams.field || '';

// camera
function updateCamera (camera) {
  ['zoom', 'pitch', 'elevation', 'yaw', 'azimuth', 'roll', 'dolly'].forEach(
    (key) => {
      if (userParams[key]) {
        camera[key](userParams[key]);
      }
      renderWindow.render();
    }
  );
}
global.updateCamera = updateCamera;

// ----------------------------------------------------------------------------
// DOM containers for UI control
// ----------------------------------------------------------------------------

const rootControllerContainer = document.createElement('div');
rootControllerContainer.setAttribute('class', style.rootController);

const addDataSetButton = document.createElement('img');
addDataSetButton.setAttribute('class', style.button);
addDataSetButton.setAttribute('src', icon);
addDataSetButton.addEventListener('click', () => {
  const isVisible = rootControllerContainer.style.display !== 'none';
  rootControllerContainer.style.display = isVisible ? 'none' : 'flex';
});

const fpsMonitor = vtkFPSMonitor.newInstance();
const fpsElm = fpsMonitor.getFpsMonitorContainer();
fpsElm.classList.add(style.fpsMonitor);

// ----------------------------------------------------------------------------
// Add class to body if iOS device
// ----------------------------------------------------------------------------

const iOS = /iPad|iPhone|iPod/.test(window.navigator.platform);

if (iOS) {
  document.querySelector('body').classList.add('is-ios-device');
}

// ----------------------------------------------------------------------------

function emptyContainer (container) {
  fpsMonitor.setContainer(null);
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }
}

global.emptyContainer = emptyContainer;
// ----------------------------------------------------------------------------

function createViewer (container) {
  const fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
    background,
    rootContainer: container,
    containerStyle: { height: '80%', width: '75%' }
  });
  renderer = fullScreenRenderer.getRenderer();
  renderWindow = fullScreenRenderer.getRenderWindow();

  global.fullScreenRenderer = fullScreenRenderer;
  global.renderer = renderer;
  global.renderWindow = renderWindow;

  renderWindow.getInteractor().setDesiredUpdateRate(15);

  container.appendChild(rootControllerContainer);
  container.appendChild(addDataSetButton);

  scalarBarActor = vtkScalarBarActor.newInstance();
  renderer.addActor(scalarBarActor);

  if (userParams.fps) {
    if (Array.isArray(userParams.fps)) {
      fpsMonitor.setMonitorVisibility(...userParams.fps);
      if (userParams.fps.length === 4) {
        fpsMonitor.setOrientation(userParams.fps[3]);
      }
    }
    fpsMonitor.setRenderWindow(renderWindow);
    fpsMonitor.setContainer(container);
    fullScreenRenderer.setResizeCallback(fpsMonitor.update);
  }
}
global.createViewer = createViewer;

// ----------------------------------------------------------------------------

function createPipeline (fileContents, name = undefined) {
  // Create UI
  const presetSelector = document.createElement('select');
  presetSelector.setAttribute('class', selectorClass);
  presetSelector.innerHTML = vtkColorMaps.rgbPresetNames
    .map(
      (name) =>
        `<option value="${name}" ${
          lutName === name ? 'selected="selected"' : ''
        }>${name}</option>`
    )
    .join('');

  const representationSelector = document.createElement('select');
  representationSelector.setAttribute('class', selectorClass);
  representationSelector.innerHTML = [
    'Hidden',
    'Points',
    'Wireframe',
    'Surface',
    'Surface with Edge'
  ]
    .map(
      (name, idx) =>
        `<option value="${idx === 0 ? 0 : 1}:${idx < 4 ? idx - 1 : 2}:${
          idx === 4 ? 1 : 0
        }">${name}</option>`
    )
    .join('');
  representationSelector.value = '1:2:0';

  const colorBySelector = document.createElement('select');
  colorBySelector.setAttribute('class', selectorClass);

  const componentSelector = document.createElement('select');
  componentSelector.setAttribute('class', selectorClass);
  componentSelector.style.display = 'none';

  const opacitySelector = document.createElement('input');
  opacitySelector.setAttribute('class', selectorClass);
  opacitySelector.setAttribute('type', 'range');
  opacitySelector.setAttribute('value', '100');
  opacitySelector.setAttribute('max', '100');
  opacitySelector.setAttribute('min', '1');

  if (name === undefined) {
    name = 'Mesh';
  }
  const labelSelector = document.createElement('label');
  labelSelector.setAttribute('class', selectorClass);
  labelSelector.innerHTML = name;

  const controlContainer = document.createElement('div');
  controlContainer.setAttribute('class', style.control);
  controlContainer.appendChild(labelSelector);
  controlContainer.appendChild(representationSelector);
  controlContainer.appendChild(presetSelector);
  controlContainer.appendChild(colorBySelector);
  controlContainer.appendChild(componentSelector);
  controlContainer.appendChild(opacitySelector);
  rootControllerContainer.appendChild(controlContainer);

  // VTK pipeline
  const vtpReader = vtkXMLPolyDataReader.newInstance();
  var buffer = Base64.toArrayBuffer(fileContents);
  vtpReader.parseAsArrayBuffer(buffer);

  const lookupTable = vtkColorTransferFunction.newInstance();
  const source = vtpReader.getOutputData(0);
  const mapper = vtkMapper.newInstance({
    interpolateScalarsBeforeMapping: false,
    useLookupTableScalarRange: true,
    lookupTable,
    scalarVisibility: false
  });
  const actor = vtkActor.newInstance();
  const scalars = source.getPointData().getScalars();
  const dataRange = [].concat(scalars ? scalars.getRange() : [0, 1]);
  let activeArray = vtkDataArray;

  // --------------------------------------------------------------------
  // Color handling
  // --------------------------------------------------------------------

  function applyPreset () {
    const preset = vtkColorMaps.getPresetByName(presetSelector.value);
    lookupTable.applyColorMap(preset);
    lookupTable.setMappingRange(dataRange[0], dataRange[1]);
    lookupTable.updateRange();
    renderWindow.render();
  }
  applyPreset();
  presetSelector.addEventListener('change', applyPreset);

  // --------------------------------------------------------------------
  // Representation handling
  // --------------------------------------------------------------------

  function updateRepresentation (event) {
    const [
      visibility,
      representation,
      edgeVisibility
    ] = event.target.value.split(':').map(Number);
    actor.getProperty().set({ representation, edgeVisibility });
    actor.setVisibility(!!visibility);
    renderWindow.render();
  }
  representationSelector.addEventListener('change', updateRepresentation);

  // --------------------------------------------------------------------
  // Opacity handling
  // --------------------------------------------------------------------

  function updateOpacity (event) {
    const opacity = Number(event.target.value) / 100;
    actor.getProperty().setOpacity(opacity);
    renderWindow.render();
  }

  opacitySelector.addEventListener('input', updateOpacity);

  // --------------------------------------------------------------------
  // ColorBy handling
  // --------------------------------------------------------------------

  const colorByOptions = [{ value: ':', label: 'Solid color' }].concat(
    source
      .getPointData()
      .getArrays()
      .map((a) => ({
        label: `(p) ${a.getName()}`,
        value: `PointData:${a.getName()}`
      })),
    source
      .getCellData()
      .getArrays()
      .map((a) => ({
        label: `(c) ${a.getName()}`,
        value: `CellData:${a.getName()}`
      }))
  );
  colorBySelector.innerHTML = colorByOptions
    .map(
      ({ label, value }) =>
        `<option value="${value}" ${
          field === value ? 'selected="selected"' : ''
        }>${label}</option>`
    )
    .join('');

  function updateColorBy (event) {
    const [location, colorByArrayName] = event.target.value.split(':');
    const interpolateScalarsBeforeMapping = location === 'PointData';
    let colorMode = ColorMode.DEFAULT;
    let scalarMode = ScalarMode.DEFAULT;
    const scalarVisibility = location.length > 0;
    if (scalarVisibility) {
      const newArray = source[`get${location}`]().getArrayByName(
        colorByArrayName
      );
      activeArray = newArray;
      const newDataRange = activeArray.getRange();
      dataRange[0] = newDataRange[0];
      dataRange[1] = newDataRange[1];
      colorMode = ColorMode.MAP_SCALARS;
      scalarMode =
        location === 'PointData'
          ? ScalarMode.USE_POINT_FIELD_DATA
          : ScalarMode.USE_CELL_FIELD_DATA;

      const numberOfComponents = activeArray.getNumberOfComponents();
      if (numberOfComponents > 1) {
        // always start on magnitude setting
        if (mapper.getLookupTable()) {
          const lut = mapper.getLookupTable();
          lut.setVectorModeToMagnitude();
        }
        componentSelector.style.display = 'block';
        const compOpts = ['Magnitude'];
        while (compOpts.length <= numberOfComponents) {
          compOpts.push(`Component ${compOpts.length}`);
        }
        componentSelector.innerHTML = compOpts
          .map((t, index) => `<option value="${index - 1}">${t}</option>`)
          .join('');
      } else {
        componentSelector.style.display = 'none';
      }
      scalarBarActor.setAxisLabel(colorByArrayName);
      scalarBarActor.setVisibility(true);
    } else {
      componentSelector.style.display = 'none';
      scalarBarActor.setVisibility(false);
    }
    mapper.set({
      colorByArrayName,
      colorMode,
      interpolateScalarsBeforeMapping,
      scalarMode,
      scalarVisibility
    });
    applyPreset();
  }
  colorBySelector.addEventListener('change', updateColorBy);
  updateColorBy({ target: colorBySelector });

  function updateColorByComponent (event) {
    if (mapper.getLookupTable()) {
      const lut = mapper.getLookupTable();
      if (event.target.value === -1) {
        lut.setVectorModeToMagnitude();
      } else {
        lut.setVectorModeToComponent();
        lut.setVectorComponent(Number(event.target.value));
        const newDataRange = activeArray.getRange(Number(event.target.value));
        dataRange[0] = newDataRange[0];
        dataRange[1] = newDataRange[1];
        lookupTable.setMappingRange(dataRange[0], dataRange[1]);
        lut.updateRange();
      }
      renderWindow.render();
    }
  }
  componentSelector.addEventListener('change', updateColorByComponent);

  // --------------------------------------------------------------------
  // Pipeline handling
  // --------------------------------------------------------------------

  actor.setMapper(mapper);
  mapper.setInputData(source);
  renderer.addActor(actor);

  scalarBarActor.setScalarsToColors(mapper.getLookupTable());

  // Manage update when lookupTable change
  const debouncedRender = debounce(renderWindow.render, 10);
  lookupTable.onModified(debouncedRender, -1);

  // First render
  renderer.resetCamera();
  renderWindow.render();

  // global.pipeline[fileName] = {
  //   actor,
  //   mapper,
  //   source,
  //   lookupTable,
  //   renderer,
  //   renderWindow,
  // };

  // Update stats
  fpsMonitor.update();
}

global.createPipeline = createPipeline;
// ----------------------------------------------------------------------------
