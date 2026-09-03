import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
} from 'typeorm';

export enum TipoSiniestro {
  REGULAR = 'regular',
  PARAMETRICO = 'parametrico',
}

export enum EstadoSiniestro {
  REPORTADO = 'reportado',
  ENRUTADO_PERITO = 'enrutado_perito',
  EN_REVISION = 'en_revision',
  APROBADO = 'aprobado',
  RECHAZADO = 'rechazado',
  PAGADO = 'pagado',
}

@Entity('siniestros')
export class Siniestro {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'enum', enum: TipoSiniestro })
  tipo!: TipoSiniestro;

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

  @Column({ type: 'jsonb', nullable: true })
  datosEventoParametrico!: Record<string, any> | null; // ej. sensor, umbral disparado

  @Column({ type: 'varchar', unique: true, nullable: true })
  claveIdempotenciaPago!: string | null; // evita duplicar el pago parametrico automatico
}
