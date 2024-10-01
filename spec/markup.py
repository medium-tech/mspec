"""
self:
  - model   (if we're defining a caluclated model field)
  - input   (workflow input)
  - state   (workflow state)
  - output  (workflow output)
  - client
    - if we're a client this is info about the local machine
    - if we're a server this is info about the remote client
  - server
    - if we're a client this is info about the remote server
    - if we're a server this is info about the local machine

control flow:
  branch (if/elif/else)
  human input
  task
    - client side
    - server side

comparison:
  eq, ne, lt, le, gt, ge

logical:
  and, or, not

convert:
  to_bool, to_int, to_float, to_str, to_list, invert

math functions:
  nums:  add, subtract, multiply, divide, power, modulo
  lists: sum, mean, median, mode, range, variance, standard deviation

list ops:
  sort, reverse
  enumerate, count
  concat, append, extend, insert
  any, all, none, map, reduce
  filter, drop, dropwhile, take, takewhile

"""