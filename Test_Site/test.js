let formidable = require('formidable');
import { fileURLToPath } from 'url';

let http = require('http');
let fs = require('fs');

// const __filename = fileURLToPath(import.meta.url);

http.createServer(function (req, res) {
  res.writeHead(200, {'Content-Type': 'text/html'});
  res.write('<form action="fileupload" method="post" enctype="multipart/form-data">');
  res.write('<input type="file" name="filetoupload"><br>');
  res.write('<input type="submit">');
  res.write('</form>');
  return res.end();
}).listen(8080);

http.createServer(function (req, res) {
  if (req.url == '/fileupload') {
    let form = new formidable.IncomingForm();
    form.parse(req, function (err, fields, files) {
      res.write('File uploaded');
      res.end();
    });
  } else {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.write('<form action="fileupload" method="post" enctype="multipart/form-data">');
    res.write('<input type="file" name="filetoupload"><br>');
    res.write('<input type="submit">');
    res.write('</form>');
    return res.end();
  }
}).listen(8080);

http.createServer(function (req, res) {
  if (req.url == '/fileupload') {
    let form = new formidable.IncomingForm();
    form.parse(req, function (err, fields, files) {
      let oldpath = files.filetoupload.filepath;
      let newpath = './pdfs' + files.filetoupload.originalFilename; // __filename?
      fs.rename(oldpath, newpath, function (err) {
        if (err) throw err;
        res.write('File uploaded and moved!');
        res.end();
      });
 });
  } else {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.write('<form action="fileupload" method="post" enctype="multipart/form-data">');
    res.write('<input type="file" name="filetoupload"><br>');
    res.write('<input type="submit">');
    res.write('</form>');
    return res.end();
  }
}).listen(8080);