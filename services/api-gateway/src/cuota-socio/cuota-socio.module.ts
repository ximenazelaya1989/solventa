import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { CuotaSocioGuard } from './cuota-socio.guard';

// EXP-008: registra la cuota por socio como guard global del gateway.
// Con RATE_LIMIT_ENABLED=false el guard no hace nada.
@Module({
  providers: [{ provide: APP_GUARD, useClass: CuotaSocioGuard }],
})
export class CuotaSocioModule {}
