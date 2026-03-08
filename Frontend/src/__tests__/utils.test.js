import {
  getProductos,
  addProducto,
  updateProducto,
  deleteProducto,
  diasParaVencer,
} from '../pages/store/inventarioStore'
import { describe, beforeEach, it, expect, jest } from '@jest/globals'
import { auth } from '../firebase.js'
import {
  addDoc,
  getDocs,
  updateDoc,
  deleteDoc,
} from 'firebase/firestore'

describe('inventarioStore', () => {
  beforeEach(() => {
    auth.currentUser = { uid: 'test_user_123' }
    jest.clearAllMocks()
  })

  it('getProductos devuelve productos desde Firestore', async () => {
    const result = await getProductos()
    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThanOrEqual(1)
    expect(result[0]).toHaveProperty('id')
  })

  it('addProducto guarda y retorna lista actualizada', async () => {
    const result = await addProducto({
      nombre: 'Leche',
      cantidad: 2,
      unidad: 'L',
      categoria: 'lacteos',
      fechaVencimiento: null,
    })

    expect(addDoc).toHaveBeenCalled()
    expect(getDocs).toHaveBeenCalled()
    expect(result.length).toBeGreaterThanOrEqual(1)
  })

  it('updateProducto actualiza por id', async () => {
    const updated = await updateProducto({
      id: 'doc-1',
      nombre: 'Harina',
      cantidad: 3,
      nombre: 'Harina Integral',
    })

    expect(updateDoc).toHaveBeenCalled()
    expect(updated.length).toBeGreaterThanOrEqual(1)
  })

  it('deleteProducto elimina por id', async () => {
    const updated = await deleteProducto('doc-1')
    expect(deleteDoc).toHaveBeenCalled()
    expect(updated.length).toBeGreaterThanOrEqual(0)
  })

  it('diasParaVencer devuelve null si no hay fecha', () => {
    expect(diasParaVencer(null)).toBeNull()
  })

  it('diasParaVencer devuelve un número positivo para fecha futura', () => {
    const future = new Date()
    future.setDate(future.getDate() + 2)
    const dias = diasParaVencer(future.toISOString().split('T')[0])

    expect(typeof dias).toBe('number')
    expect(dias).toBeGreaterThanOrEqual(1)
    expect(dias).toBeLessThanOrEqual(3)
  })
})
