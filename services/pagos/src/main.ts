import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { cargarZona, instancia } from './common/instancia';

async function bootstrap() {
  await cargarZona();
  const app = await NestFactory.create(AppModule);
  await app.listen(process.env.PORT ?? 3000, '0.0.0.0');
  console.log(
    JSON.stringify({
      ts: new Date().toISOString(),
      evento: 'replica_iniciada',
      replica: instancia(),
      retryIdempotency: process.env.RETRY_IDEMPOTENCY_ENABLED === 'true',
    }),
  );
}
bootstrap();
