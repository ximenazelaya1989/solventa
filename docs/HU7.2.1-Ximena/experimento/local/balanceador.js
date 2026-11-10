// Balanceador minimo para el ensayo local de EXP-006: round-robin entre las
// replicas de Pagos, sin reintentos (como el ALB) y con health check a /health
// cada 5 s; una replica sale de rotacion tras 2 fallas seguidas.
const http = require('http');

const destinos = (process.env.DESTINOS ?? 'localhost:3001,localhost:3002')
  .split(',')
  .map((d) => {
    const [host, port] = d.split(':');
    return { host, port: Number(port), fallas: 0 };
  });
let turno = 0;

setInterval(() => {
  for (const d of destinos) {
    const req = http.get({ host: d.host, port: d.port, path: '/health', timeout: 2000 }, (r) => {
      r.resume();
      d.fallas = r.statusCode === 200 ? 0 : d.fallas + 1;
    });
    req.on('timeout', () => req.destroy());
    req.on('error', () => d.fallas++);
  }
}, 5000);

http
  .createServer((req, res) => {
    const sanos = destinos.filter((d) => d.fallas < 2);
    const lista = sanos.length ? sanos : destinos;
    const d = lista[turno++ % lista.length];
    const proxy = http.request(
      { host: d.host, port: d.port, path: req.url, method: req.method, headers: req.headers },
      (r) => {
        res.writeHead(r.statusCode, r.headers);
        r.pipe(res);
      },
    );
    proxy.on('error', () => {
      res.writeHead(502);
      res.end('bad gateway');
    });
    req.pipe(proxy);
  })
  .listen(3000, () => console.log('balanceador escuchando en 3000'));
