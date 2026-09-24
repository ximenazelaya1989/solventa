import { Injectable, RequestTimeoutException } from '@nestjs/common';

const TIMEOUT_MS_POR_DEFECTO = 700;

@Injectable()
export class OrquestadorService {
  // TODO(integraciones): reintentos con backoff, respaldo en cache de solo
  // lectura y un semaforo por dependencia (limite configurable por variable
  // de entorno) -- por ahora solo se implementa el timeout duro
  async llamar<T>(
    dependencia: string,
    fn: () => Promise<T>,
    opciones?: { timeoutMs?: number },
  ): Promise<T> {
    const timeoutMs = opciones?.timeoutMs ?? TIMEOUT_MS_POR_DEFECTO;

    let temporizador: ReturnType<typeof setTimeout>;
    const timeout = new Promise<never>((_resolve, reject) => {
      temporizador = setTimeout(() => {
        reject(
          new RequestTimeoutException(
            `Timeout llamando a la dependencia "${dependencia}" (${timeoutMs}ms)`,
          ),
        );
      }, timeoutMs);
    });

    try {
      return await Promise.race([fn(), timeout]);
    } finally {
      clearTimeout(temporizador!);
    }
  }
}
