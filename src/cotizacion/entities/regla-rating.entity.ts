import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn } from 'typeorm';

/**
 * Version de reglas de rating. Se publica una fila nueva por cada version;
 * nunca se sobrescribe una version existente (config inmutable y versionada,
 * desacoplada del binario desplegado).
 */
@Entity('reglas_rating')
export class ReglaRating {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'int', unique: true })
  version!: number;

  @Column({ type: 'jsonb' })
  factores!: Record<string, number>;

  // Solo se usa para el experimento: simula una version defectuosa
  // (por ejemplo, una regla mal cargada por error humano) sin tener que
  // fabricar JSON realmente invalido.
  @Column({ type: 'boolean', default: false })
  fallaSanityCheck!: boolean;

  @CreateDateColumn()
  creadaEn!: Date;
}