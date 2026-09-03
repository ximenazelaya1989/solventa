import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity('perfiles_riesgo')
export class PerfilRiesgo {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'float' })
  score!: number;

  @Column({ type: 'jsonb', nullable: true })
  señalesOpenFinance!: Record<string, any>;

  @Column({ type: 'uuid' })
  clienteId!: string; 
}