import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import { randomUUID } from 'crypto';
import request from 'supertest';
import { DataSource } from 'typeorm';
import { AppModule } from './../src/app.module';

describe('Desembolsos e idempotencia (e2e)', () => {
  let app: INestApplication;
  let dataSource: DataSource;

  const contarPagos = async (): Promise<number> => {
    const filas = await dataSource.query('SELECT count(*)::int AS n FROM pagos');
    return filas[0].n;
  };

  beforeAll(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );
    await app.init();
    dataSource = app.get(DataSource);
  });

  beforeEach(async () => {
    await dataSource.query('TRUNCATE TABLE pagos');
  });

  afterAll(async () => {
    await app.close();
  });

  it('F01: un desembolso valido responde 201 y guarda 1 fila', async () => {
    const siniestroId = randomUUID();

    const res = await request(app.getHttpServer())
      .post('/desembolsos')
      .send({ siniestroId, monto: 1500.5 })
      .expect(201);

    expect(res.body.siniestroId).toBe(siniestroId);
    expect(await contarPagos()).toBe(1);
  });

  it('F02: el mismo siniestroId dos veces devuelve el mismo pago y 1 sola fila', async () => {
    const siniestroId = randomUUID();
    const enviar = () =>
      request(app.getHttpServer())
        .post('/desembolsos')
        .send({ siniestroId, monto: 900 })
        .expect(201);

    const primero = await enviar();
    const segundo = await enviar();

    expect(segundo.body.id).toBe(primero.body.id);
    expect(await contarPagos()).toBe(1);
  });

  it('F03: 50 pedidos simultaneos con el mismo siniestroId dejan 1 fila y 0 errores', async () => {
    const siniestroId = randomUUID();

    const respuestas = await Promise.all(
      Array.from({ length: 50 }, () =>
        request(app.getHttpServer())
          .post('/desembolsos')
          .send({ siniestroId, monto: 700 }),
      ),
    );

    expect(respuestas.every((r) => r.status === 201)).toBe(true);
    expect(new Set(respuestas.map((r) => r.body.id)).size).toBe(1);
    expect(await contarPagos()).toBe(1);
  });

  it('F04: monto negativo o siniestroId invalido responde 400 y no guarda nada', async () => {
    await request(app.getHttpServer())
      .post('/desembolsos')
      .send({ siniestroId: randomUUID(), monto: -5 })
      .expect(400);

    await request(app.getHttpServer())
      .post('/desembolsos')
      .send({ siniestroId: 'no-es-un-uuid', monto: 100 })
      .expect(400);

    expect(await contarPagos()).toBe(0);
  });

  it('F05: /health responde 200 con la base de datos arriba', async () => {
    await request(app.getHttpServer())
      .get('/health')
      .expect(200)
      .expect({ status: 'ok' });
  });

  it('F06: /health deja de responder 200 cuando la base de datos no esta disponible', async () => {
    await dataSource.destroy();

    const res = await request(app.getHttpServer()).get('/health');

    expect(res.status).not.toBe(200);
  });
});
