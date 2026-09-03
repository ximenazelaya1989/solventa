import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

export enum EstadoConsentimiento {
  ACTIVO = 'activo',
  REVOCADO = 'revocado',
}

@Entity('consentimientos')
export class Consentimiento {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'varchar' })
  fuente!: string; // ej. Open Finance

  @Column({ type: 'varchar' })
  alcance!: string; // scope de datos autorizados

  @Column({ type: 'enum', enum: EstadoConsentimiento, default: EstadoConsentimiento.ACTIVO })
  estado!: EstadoConsentimiento;

  @Column({ type: 'uuid' })
  clienteId!: string; 
}