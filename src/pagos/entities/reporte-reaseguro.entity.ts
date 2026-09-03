import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

export enum EstadoEnvioReaseguro {
  PENDIENTE = 'pendiente',
  ENVIADO = 'enviado',
  VALIDADO = 'validado',
  RECHAZADO = 'rechazado',
}

@Entity('reportes_reaseguro')
export class ReporteReaseguro {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'uuid' })
  reaseguradoraId!: string;

  @Column({ type: 'date' })
  periodoInicio!: string;

  @Column({ type: 'date' })
  periodoFin!: string;

  @Column({ type: 'varchar' })
  formato!: string; // ej. ACORD

  @Column({
    type: 'enum',
    enum: EstadoEnvioReaseguro,
    default: EstadoEnvioReaseguro.PENDIENTE,
  })
  estado!: EstadoEnvioReaseguro;

  @Column({ type: 'int', nullable: true })
  volumenRegistros!: number | null;

  @Column({ type: 'float', nullable: true })
  porcentajeExactitud!: number | null;

  @Column({ type: 'jsonb' })
  payload!: Record<string, any>; // datos de cartera y siniestralidad enviados
}
