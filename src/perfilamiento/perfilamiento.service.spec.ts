import { Test } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { PerfilRiesgo } from './entities/perfil-riesgo.entity';
import { PerfilamientoService } from './perfilamiento.service';

describe('PerfilamientoService', () => {
  const repository = {
    upsert: jest.fn(),
    findOneByOrFail: jest.fn(),
  };
  let service: PerfilamientoService;

  beforeEach(async () => {
    jest.clearAllMocks();
    const module = await Test.createTestingModule({
      providers: [
        PerfilamientoService,
        { provide: getRepositoryToken(PerfilRiesgo), useValue: repository },
      ],
    }).compile();
    service = module.get(PerfilamientoService);
  });

  it('recalcula y persiste un perfil de forma idempotente por cliente', async () => {
    repository.upsert.mockResolvedValue({ identifiers: [{ id: 'perfil-1' }] });
    repository.findOneByOrFail.mockResolvedValue({
      id: 'perfil-1',
      clienteId: '11111111-1111-4111-8111-111111111111',
      score: 53.25,
    });

    const perfil = await service.reprocesar({
      clienteId: '11111111-1111-4111-8111-111111111111',
      señalesOpenData: {
        ingresoMensual: 10_000_000,
        deudaTotal: 50_000_000,
        indicePago: 0.75,
      },
    });

    expect(repository.upsert).toHaveBeenCalledWith(
      expect.objectContaining({ score: 58.75 }),
      ['clienteId'],
    );
    expect(perfil.id).toBe('perfil-1');
  });
});
