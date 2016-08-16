var fs = require('fs');
try {
  var webshot = require('webshot');
} catch(e) {
  // use exit code 2 to indicate missing module
  process.exit(2);
}

var options = {
  windowSize: {
    width: 1920,
    height: 1080
  },
  shotSize: {
    width: 'all',
    height: 'all'
  },
  captureSelector: '.left1',
  customCSS: '#comments { display: none; }'
};

var optionsSmph = {
  windowSize: {
    width: 360,
    height: 640
  },
  shotSize: {
    width: 'all',
    height: 'all'
  },
  captureSelector: '.unit',
  streamType: 'png',
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X)'
    + ' AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3'
};

var renderStream = webshot(process.argv[2], optionsSmph);
renderStream.on('data', function(data) {
  process.stdout.write(data.toString('binary'), 'binary');
});



/*
webshot(smph(process.argv[2]), process.argv[3], optionsSmph, function(err) {
  if (err) return console.log(err);
  console.log('Captured screenshot!');
});


var renderStream = webshot(smph(url), optionsSmph);
var file = fs.createWriteStream(process.argv[3], {encoding: 'binary'});
renderStream.on('data', function(data) {
  file.write(data.toString('binary'), 'binary');
});
*/
