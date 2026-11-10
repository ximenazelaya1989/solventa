import { Entity, PrimaryGeneratedColumn, Column, Unique } from 'typeorm';

@Entity('cesiones_poliza')
@Unique(['polizaId', 'reaseguradoraId'])
export class CesionPoliza {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'uuid' })
  polizaId!: string;

  @Column({ type: 'uuid' })
  reaseguradoraId!: string;
}
