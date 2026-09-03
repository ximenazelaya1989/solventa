import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

export enum EstadoDesembolso {
  PENDIENTE = 'pendiente',
  PROCESADO = 'procesado',
  FALLIDO = 'fallido',
}

@Entity('desembolsos')
export class Desembolso {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'float' })
  monto!: number;

  @Column({ type: 'varchar' })
  moneda!: string; // ej. USD

  @Column({
    type: 'enum',
    enum: EstadoDesembolso,
    default: EstadoDesembolso.PENDIENTE,
  })
  estado!: EstadoDesembolso;

  @Column({ type: 'varchar', unique: true })
  claveIdempotencia!: string; // evita duplicar o perder el desembolso

  @Column({ type: 'uuid' })
  siniestroId!: string;

  @Column({ type: 'timestamptz', nullable: true })
  fechaProcesado!: Date | null;
}
