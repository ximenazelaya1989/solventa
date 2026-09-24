import { Module } from '@nestjs/common';
import { OrquestadorService } from './orquestador.service';

@Module({
  providers: [OrquestadorService],
  exports: [OrquestadorService],
})
export class IntegracionesModule {}
