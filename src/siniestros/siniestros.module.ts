import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Siniestro } from './entities/siniestro.entity';
import { Perito } from './entities/perito.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Siniestro, Perito])],
})
export class SiniestrosModule {}
