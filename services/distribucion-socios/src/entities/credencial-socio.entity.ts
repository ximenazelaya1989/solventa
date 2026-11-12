import { Column, Entity, PrimaryGeneratedColumn } from 'typeorm';

// EXP-010 (HU5.1.1, Génesis). Tabla nueva: relaciona la aplicacion de un socio
// en Amazon Cognito (claim client_id del token) con el socio de distribucion.
// No modifica la tabla socios_distribucion de la base compartida.
@Entity('credenciales_socio')
export class CredencialSocio {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'uuid' })
  socioId!: string;

  @Column({ type: 'varchar', unique: true })
  cognitoClientId!: string;
}
