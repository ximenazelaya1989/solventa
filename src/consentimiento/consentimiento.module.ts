import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Consentimiento } from './entities/consentimiento.entity';
import { ConsentimientoService } from './consentimiento.service';
import { ConsentimientoController } from './consentimiento.controller';

@Module({
  imports: [TypeOrmModule.forFeature([Consentimiento])],
  controllers: [ConsentimientoController],
  providers: [ConsentimientoService],
  exports: [ConsentimientoService],
})
export class ConsentimientoModule {}
