const mockAxios = {
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: { slots: [], win_projection: null } })),
  create: () => mockAxios
};

export default mockAxios;
export const get = mockAxios.get;
export const post = mockAxios.post;
