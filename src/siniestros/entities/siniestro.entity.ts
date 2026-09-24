import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  TableInheritance,
} from 'typeorm';

export enum EstadoSiniestro {
  REPORTADO = 'reportado',
  ENRUTADO_PERITO = 'enrutado_perito',
  EN_REVISION = 'en_revision',
  APROBADO = 'aprobado',
  RECHAZADO = 'rechazado',
  PAGADO = 'pagado',
}

@Entity('siniestros')
@TableInheritance({ column: { type: 'varchar', name: 'tipo' } })
export abstract class Siniestro {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({
    type: 'enum',
    enum: EstadoSiniestro,
    default: EstadoSiniestro.REPORTADO,
  })
  estado!: EstadoSiniestro;

  @Column({ type: 'uuid' })
  clienteId!: string;

  @Column({ type: 'uuid' })
  polizaId!: string;

  @Column({ type: 'uuid', nullable: true })
  peritoId!: string | null;

  @CreateDateColumn({ type: 'timestamptz' })
  fechaReporte!: Date;

  @Column({ type: 'timestamptz', nullable: true })
  fechaEnrutamiento!: Date | null;

  @Column({ type: 'timestamptz', nullable: true })
  fechaPago!: Date | null;
}
