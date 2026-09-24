import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Siniestro } from './entities/siniestro.entity';
import { SiniestroAsistido } from './entities/siniestro-asistido.entity';
import { SiniestroParametrico } from './entities/siniestro-parametrico.entity';
import { Perito } from './entities/perito.entity';
import { SiniestrosService } from './siniestros.service';
import { SiniestrosController } from './siniestros.controller';
import { PolizasModule } from '../polizas/polizas.module';
import { PagosModule } from '../pagos/pagos.module';
import { AnaliticaFraudeModule } from '../analitica-fraude/analitica-fraude.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      Siniestro,
      SiniestroAsistido,
      SiniestroParametrico,
      Perito,
    ]),
    PolizasModule,
    PagosModule,
    AnaliticaFraudeModule,
  ],
  controllers: [SiniestrosController],
  providers: [SiniestrosService],
  exports: [SiniestrosService],
})
export class SiniestrosModule {}
