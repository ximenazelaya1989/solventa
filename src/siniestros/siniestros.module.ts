import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Siniestro } from './entities/siniestro.entity';
import { SiniestroAsistido } from './entities/siniestro-asistido.entity';
import { SiniestroParametrico } from './entities/siniestro-parametrico.entity';
import { Perito } from './entities/perito.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      Siniestro,
      SiniestroAsistido,
      SiniestroParametrico,
      Perito,
    ]),
  ],
})
export class SiniestrosModule {}
