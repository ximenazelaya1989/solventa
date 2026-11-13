import Redis from 'ioredis';

// EXP-008 (HU5.1.2, Daniela): token bucket por socio guardado en Redis.
//
// Cada socio tiene un balde con `capacidad` fichas que se rellena a `tasa`
// fichas por segundo. Cada peticion consume una ficha; si no hay, se rechaza.
// Todo ocurre dentro de un script Lua, que Redis ejecuta de forma atomica:
// dos replicas del gateway no pueden gastar la misma ficha. La hora la pone
// Redis (TIME), asi que no importa el reloj de cada replica.
const SCRIPT_TOKEN_BUCKET = `
local tasa = tonumber(ARGV[1])
local capacidad = tonumber(ARGV[2])
local t = redis.call('TIME')
local ahora = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
local datos = redis.call('HMGET', KEYS[1], 'fichas', 'ts')
local fichas = tonumber(datos[1])
local ts = tonumber(datos[2])
if fichas == nil then
  fichas = capacidad
  ts = ahora
end
fichas = math.min(capacidad, fichas + math.max(0, ahora - ts) * tasa / 1000)
local permitido = 0
local espera_ms = 0
if fichas >= 1 then
  fichas = fichas - 1
  permitido = 1
else
  espera_ms = math.ceil((1 - fichas) * 1000 / tasa)
end
redis.call('HSET', KEYS[1], 'fichas', fichas, 'ts', ahora)
redis.call('PEXPIRE', KEYS[1], math.ceil(capacidad * 1000 / tasa) + 1000)
return { permitido, math.floor(fichas), espera_ms }
`;

export interface ResultadoCuota {
  permitido: boolean;
  restantes: number;
  esperaMs: number;
}

type RedisConCuota = Redis & {
  tomarFicha(clave: string, tasa: number, capacidad: number): Promise<number[]>;
};

export class TokenBucket {
  private readonly redis: RedisConCuota;

  constructor(url: string, timeoutMs: number) {
    // Sin cola offline ni reintentos: si Redis no responde rapido, la peticion
    // no espera (el guard decide que hacer con el error).
    this.redis = new Redis(url, {
      enableOfflineQueue: false,
      maxRetriesPerRequest: 0,
      commandTimeout: timeoutMs,
    }) as RedisConCuota;
    this.redis.on('error', () => undefined); // el guard registra los fallos
    this.redis.defineCommand('tomarFicha', {
      numberOfKeys: 1,
      lua: SCRIPT_TOKEN_BUCKET,
    });
  }

  async tomar(clave: string, tasa: number, capacidad: number): Promise<ResultadoCuota> {
    const [permitido, restantes, esperaMs] = await this.redis.tomarFicha(clave, tasa, capacidad);
    return { permitido: permitido === 1, restantes, esperaMs };
  }
}
