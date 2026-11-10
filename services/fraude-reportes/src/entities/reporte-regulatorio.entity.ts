import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

export enum EstadoEnvioReporte {
  PENDIENTE = 'pendiente',
  ENVIADO = 'enviado',
  VALIDADO = 'validado',
  RECHAZADO = 'rechazado',
}

@Entity('reportes_regulatorios')
export class ReporteRegulatorio {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'varchar' })
  destinatario!: string; // regulador o reaseguradora

  @Column({ type: 'date' })
  periodoInicio!: string;

  @Column({ type: 'date' })
  periodoFin!: string;

  @Column({ type: 'varchar' })
  formato!: string; // ej. ACORD

  @Column({
    type: 'enum',
    enum: EstadoEnvioReporte,
    default: EstadoEnvioReporte.PENDIENTE,
  })
  estado!: EstadoEnvioReporte;

  @Column({ type: 'int', nullable: true })
  volumenRegistros!: number | null;

  @Column({ type: 'float', nullable: true })
  porcentajeExactitud!: number | null;

  @Column({ type: 'jsonb' })
  payload!: Record<string, any>; // datos de cartera y siniestralidad enviados
}
