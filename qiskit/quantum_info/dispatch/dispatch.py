# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Dispatch class"""

from typing import Optional, Union, Tuple


class Dispatch:
    """Dispatch Numpy ufuncs to multiple array backends."""

    # Registered backend names
    REGISTERED_BACKENDS = tuple()

    # Set version of registered backend name strings
    _REGISTERED_BACKENDS = set()

    # Registered backend array types
    REGISTERED_TYPES = tuple()

    # Set version of registered backend array types
    _REGISTERED_TYPES = {}

    # Default backend. If None the backend of the input array is used.
    DEFAULT_BACKEND = None

    # Dispatch table from backend name to asarray function
    ASARRAY_DISPATCH = {}

    # Dispatch table from backend name to repr function
    REPR_DISPATCH = {}

    # Dispatch table from backend name to array_ufunc dispatcher
    ARRAY_UFUNC_DISPATCH = {}

    # Dispatch table from backend name to array_function dispatcher
    ARRAY_FUNCTION_DISPATCH = {}

    @classmethod
    def backend(cls, array: any, fallback: Optional[str] = None) -> str:
        """Return the registered backend string of a array object.

        Args:
            array: an array object.
            fallback: If this value if array type is not registered.

        Returns:
            str: The array backend name if the array type is registered,
                 or `use_default=True` and the type is not registered.
            None: If `use_default=False` and the array type is not registered.

        Raises:
            ValueError: if fallback backend is not valid.
        """
        backend = cls._REGISTERED_TYPES.get(type(array), None)
        if backend is not None:
            return backend
        if fallback is None or fallback in cls._REGISTERED_BACKENDS:
            return fallback
        raise ValueError("fallback '{}' is not a registered backend.".format(fallback))

    @classmethod
    def validate_backend(cls, backend: str):
        """Raise an exception if backend is not registered.

        Args:
            backend: array backend name.

        Raises:
            ValueError: if backend is not registered.
        """
        if backend not in cls._REGISTERED_BACKENDS:
            registered = cls.REGISTERED_BACKENDS if cls.REGISTERED_BACKENDS else None
            raise ValueError(
                "'{}' is not a registered array backends (registered backends: {})"
                .format(backend, registered))

    @classmethod
    def array_ufunc(cls, backend: str, ufunc: callable,
                    method: str) -> callable:
        """Return the ufunc for the specified array backend

        Args:
            backend: the array backend name.
            ufunc: the numpy ufunc.
            method: the ufunc method.

        Returns:
            callable: the ufunc for the specified array backend.
        """
        return cls.ARRAY_UFUNC_DISPATCH[backend](ufunc, method)

    @classmethod
    def repr(cls, backend: str) -> callable:
        """Return the ufunc for the specified array backend

        Args:
            backend: the array backend name.

        Returns:
            callable: the repr function for the specified array backend.
        """
        return cls.REPR_DISPATCH[backend]

    @classmethod
    def array_function(cls, backend: str, func: callable) -> callable:
        """Return the array function for the specified array backend

        Args:
            backend: the array backend name.
            func: the numpy array function.

        Returns:
            callable: the function for the specified array backend.
        """
        return cls.ARRAY_FUNCTION_DISPATCH[backend](func)

    @classmethod
    def register_types(cls, name: str, array_types: Union[any, Tuple[any]]):
        """Register an asarray array backend.

        Args:
            name: A string to identify the array backend.
            array_types: A class or list of classes to associate
                         with the array backend.
        """
        cls._REGISTERED_BACKENDS.add(name)
        cls.REGISTERED_BACKENDS = tuple(cls._REGISTERED_BACKENDS)
        if not isinstance(array_types, (list, tuple)):
            array_types = [array_types]
        for atype in array_types:
            cls._REGISTERED_TYPES[atype] = name
        cls.REGISTERED_TYPES = tuple(cls._REGISTERED_TYPES.keys())


    @classmethod
    def register_asarray(cls,
                         name: str,
                         array_types: Optional[Union[any, Tuple[any]]] = None
                         ) -> callable:
        """Decorator to register an asarray function for an array backend.

        The function being wrapped must have signature
        `func(arg, dtype=None, order=None)`.

        Args:
            name: A string to identify the array backend.
            array_types: Optional, the array types to register
                         for the backend.

        Returns:
            callable: the decorated function.
        """
        if array_types:
            cls.register_types(name, array_types)

        def decorator(func):
            cls.ASARRAY_DISPATCH[name] = func
            return func

        return decorator

    @classmethod
    def register_repr(cls,
                      name: str,
                      array_types: Optional[Union[any, Tuple[any]]] = None
                      ) -> callable:
        """Decorator to register an asarray function for an array backend.

        The function being wrapped must have signature
        `func(arg, dtype=None, order=None)`.

        Args:
            name: A string to identify the array backend.
            array_types: Optional, the array types to register
                         for the backend.

        Returns:
            callable: the decorated function.
        """
        if array_types:
            cls.register_types(name, array_types)

        def decorator(func):
            cls.REPR_DISPATCH[name] = func
            return func

        return decorator

    @classmethod
    def register_array_ufunc(
            cls, name: str,
            array_types: Optional[Union[any, Tuple[any]]] = None) -> callable:
        """Decorator to register a ufunc dispatch function.

        This is used for handling of dispatch of Numpy ufuncs using
        `__array_ufunc__`. The function being wrapped must have
        signature `f(ufunc, method) -> callable(*args, **kwargs)`

        Args:
            name: A string to identify the array backend.
            array_types: Optional, the array types to register
                         for the backend.

        Returns:
            callable: the decorated function.
        """
        if array_types:
            cls.register_types(name, array_types)

        def decorator(func):
            cls.ARRAY_UFUNC_DISPATCH[name] = func
            return func

        return decorator

    @classmethod
    def register_array_function(
            cls, name: str,
            array_types: Optional[Union[any, Tuple[any]]] = None) -> callable:
        """Decorator to register an array function dispatch function.

        This is used for handling of dispatch of Numpy functions using
        `__array_function__`. The function being wrapped must have
        signature `f(func) -> callable(*args, **kwargs)`.

        Args:
            name: A string to identify the array backend.
            array_types: Optional, the array types to register
                         for the backend.

        Returns:
            callable: the decorated function.
        """
        if array_types:
            cls.register_types(name, array_types)

        def decorator(func):
            cls.ARRAY_FUNCTION_DISPATCH[name] = func
            return func

        return decorator

    @staticmethod
    def implements(np_function, dispatch_dict):
        """Register a numpy __array_function__ implementation."""
        def decorator(func):
            dispatch_dict[np_function] = func
            return func
        return decorator


# Public functions

def set_default_backend(backend: Optional[str] = None):
    """Set the default array backend."""
    if backend is not None:
        Dispatch.validate_backend(backend)
    Dispatch.DEFAULT_BACKEND = backend


def default_backend():
    """Return the default array backend."""
    return Dispatch.DEFAULT_BACKEND


def backend_types():
    """Return tuple of array backend types"""
    return Dispatch.REGISTERED_TYPES


def available_backends():
    """Return a tuple of available array backends"""
    return Dispatch.REGISTERED_BACKENDS


def asarray(array: any,
            dtype: Optional[any] = None,
            order: Optional[str] = None,
            backend: Optional[str] = None) -> any:
    """Convert input array to an array on the specified backend.

    This functions like `numpy.asarray` but optionally supports
    casting to other registered array backends.

    Args:
        array: An array_like input.
        dtype: Optional. The dtype of the returned array. This value
                must be supported by the specified array backend.
        order: Optional. The array order. This value must be supported
                by the specified array backend.
        backend: A registered array backend name. If None the
                    default array backend will be used.

    Returns:
        array: an array object of the form specified by the backend
                kwarg.
    """
    if backend:
        Dispatch.validate_backend(backend)
    else:
        if  Dispatch.DEFAULT_BACKEND:
            backend = Dispatch.DEFAULT_BACKEND
        else:
            backend = Dispatch.backend(array, fallback='numpy')
    return  Dispatch.ASARRAY_DISPATCH[backend](array, dtype=dtype, order=order)
