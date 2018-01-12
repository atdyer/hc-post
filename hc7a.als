
module hc7a -- add a refinement check, show spec is refined by impl

-- let joints have a state "balanced" (a Boolean for each vertex), and
-- include just one type of pending operation (a carryover, another
-- Boolean, on each edge) ... assume that release and distribute are
-- combined into an atomic operation.  Then, a carryover operation,
-- when processed, makes a neighbor joint unbalanced.

/*
 * A model of the Hardy Cross method of moment distribution
 *
 * Date: January 7, 2018
 * Alloy Analyzer 4.2_2015-02-22 (build date: 2015-02-22 18:21 EST)
 *
 */

open util/graph [Vertex]
open util/ordering [State] as so

abstract sig Bool {}
one sig True, False extends Bool {}

abstract sig Counter {}
one sig Test, Send, Receive extends Counter {}

sig State {}

sig Vertex {
  pc: Counter one -> State,     -- program counter only for implementation I
  balanced: Bool one -> State,  -- associated member ends balance
  end: Vertex -> Bool -> State  -- member ends and carryover from u to v
}

-- the set of edges is defined by x-y vertex pairs that have ends
-- associated with them
fun edges: Vertex->Vertex {
  { x, y: Vertex | some end[x, y] }
}

-- min topological requirements for a building structure (overapproximation)
fact { noSelfLoops[edges] and undirected[edges] and stronglyConnected[edges] }

-- one carryover value associated with each member end in each state
fact { all x, y: Vertex, s: State | some end[x, y] => one end[x, y].s }

------------------------------------------------------------------------------

-- Specification S

pred init_S [s: State] {
  all x: Vertex |
    x.balanced.s = False   -- all unbalanced, but could leave undetermined
  all x, y: Vertex |
    x->y in edges => end[x, y].s = False   -- no pending carryovers
}

pred step_S [s, s': State] {
  (some x: Vertex | release[x, s, s'])
  or (some x, y: Vertex | x->y in edges and carryover[x, y, s, s'])
  or stutter[s, s']
}

pred stutter [s, s': State] {
  all x: Vertex |
    x.balanced.s' = x.balanced.s
  all x, y: Vertex |
    x->y in edges => end[x, y].s' = end[x, y].s
}

-- a release can happen only when u is unbalanced and has no pending
-- carryover operations that it needs to perform
pred release [u: Vertex, s, s': State] {
  u.balanced.s = False and no pending[u, s]
  all x: Vertex |
    x.balanced.s' = (x = u => True else x.balanced.s)
  all x, y: Vertex | x->y in edges =>
    end[x, y].s' = (x = u => True else end[x, y].s)
}

-- edges x->y where x = u with a pending operation (that makes y unbalanced)
fun pending [u: Vertex, s: State]: Vertex->Vertex {
  { x, y: Vertex | x->y in edges and x = u and end[x, y].s = True }
}

-- makes v unbalanced, discharging pending u->v carryover operation
pred carryover [u, v: Vertex, s, s': State] {
  end[u, v].s = True
  all y: Vertex |
    y.balanced.s' = (y = v => False else y.balanced.s)
  all x, y: Vertex | x->y in edges =>
    end[x, y].s' = (x = u and y = v => False else end[x, y].s)
}

------------------------------------------------------------------------------

-- generate some instances

pred show_S {
  no x: Vertex | x = A or x = B or x = C -- disable Baugh/Liu example
  #Vertex > 1
  init_S[so/first]
  all s: State - so/last | step_S[s, s.so/next]
}

run show_S for 4 Vertex, 10 State

-- example from Baugh/Liu

lone sig A, B, C extends Vertex {}

-- from Baugh/Liu (except that, here, every joint can be released)
pred example {
  all x: Vertex | x = A or x = B or x = C -- or declare Vertex abstract
  A->B in edges
  B->C in edges
  A->C not in edges
}

pred show_S_ex {
  init_S[so/first]
  all s: State - so/last | step_S[s, s.so/next]
  example
  my_steps
--  my_steps_broken
}

run show_S_ex for 3 Vertex, 11 State -- 11 states needed for my_steps

-- a sample trace with simultaneous releases, followed by carryovers,
-- releases, and so on ...
pred my_steps {
  let s0 = so/first, s1 = s0.so/next, s2 = s1.so/next, s3 = s2.so/next,
    s4 = s3.so/next, s5 = s4.so/next, s6 = s5.so/next, s7 = s6.so/next,
    s8 = s7.so/next, s9 = s8.so/next, s10 = s9.so/next {
      release[A, s0, s1]
      release[B, s1, s2]
      release[C, s2, s3]
      carryover[A, B, s3, s4]
      carryover[B, C, s4, s5]
      carryover[B, A, s5, s6]
      carryover[C, B, s6, s7]
      release[A, s7, s8]
      release[B, s8, s9]
      release[C, s9, s10]
  }
}

pred my_steps_broken {
  let s0 = so/first, s1 = s0.so/next, s2 = s1.so/next, s3 = s2.so/next,
    s4 = s3.so/next, s5 = s4.so/next, s6 = s5.so/next {
      release[A, s0, s1]
      release[B, s1, s2]
      release[C, s2, s3]
      carryover[A, B, s3, s4]
      carryover[B, C, s4, s5]
      release[B, s5, s6]      -- can't release B, has a pending carryover
  }
}

------------------------------------------------------------------------------

-- Implementation I: synchronous message passing between concurrent processes

pred init_I [s: State] {
  init_S[s]
  all x: Vertex | x.pc.s = Test
}

pred step_I [s, s': State] {
  some x: Vertex | process[x, s, s']
}

-- associate a concurrent process with each vertex
pred process [u: Vertex, s, s': State] {
  test[u, s, s'] or leave_send[u, s, s'] or leave_receive[u, s, s']
  or one v: Vertex | u->v in edges and synch[u, v, s, s']
}

pred test [u: Vertex, s, s': State] {
  u.pc.s = Test
  enter_send[u, s, s'] or enter_receive[u, s, s']
}

pred enter_send[u: Vertex, s, s': State] {
  u.balanced.s = False
  u.pc.s' = Send
  u.balanced.s' = True
  all x, y: Vertex | x->y in edges =>
    end[x, y].s' = (x = u => True else end[x, y].s)
  unchanged[Vertex - u, none->none, s, s']
}

pred leave_send [u: Vertex, s, s': State] {
  u.pc.s = Send and no { v: Vertex | end[u, v].s = True }
  u.pc.s' = Test
  u.balanced.s' = u.balanced.s -- was made True in test, leave as is
  unchanged[Vertex - u, edges, s, s']
}

pred enter_receive[u: Vertex, s, s': State] {
  some x: Vertex | end[x, u].s = True and x.pc.s = Send
  u.pc.s' = Receive
  u.balanced.s' = u.balanced.s
  unchanged[Vertex - u, edges, s, s']
}

pred leave_receive [v: Vertex, s, s': State] {
  v.pc.s = Receive and no { u: Vertex | end[u, v].s = True }
  v.pc.s' = Test
  v.balanced.s' = v.balanced.s -- was made False on synch, leave as is
  unchanged[Vertex - v, edges, s, s']
}

pred synch [u, v: Vertex, s, s': State] {
  u.pc.s = Send and v.pc.s = Receive and end[u, v].s = True
  v.pc.s' = v.pc.s        -- receiver remains in receive mode    
  v.balanced.s' = False   -- but becomes unbalanced
  end[u, v].s' = False    -- and the edge token is consumed
  unchanged[Vertex - v, edges - u->v, s, s']
}

pred unchanged [vs: set Vertex, es: Vertex->Vertex, s, s': State] {
  all x: vs |
    x.pc.s' = x.pc.s and x.balanced.s' = x.balanced.s
  all x, y: Vertex |
    x->y in es => end[x, y].s' = end[x, y].s
}

------------------------------------------------------------------------------

-- generate some instances

pred show_I_ex {
  init_I[so/first]
  all s: State - so/last | step_I[s, s.so/next]
  example
  my_steps2 -- comment out to generate all traces
}

run show_I_ex for 3 Vertex, 9 State

run show_I_ex for 3 Vertex, 40 State

-- show (an instance of) the relationship between S and I
pred my_steps2 {
  let s0 = so/first, s1 = s0.so/next, s2 = s1.so/next, s3 = s2.so/next,
    s4 = s3.so/next, s5 = s4.so/next, s6 = s5.so/next, s7 = s6.so/next,
    s8 = s7.so/next {
      test[B, s0, s1] and release[B, s0, s1]     -- balance B, send to A & C
      test[A, s1, s2] and stutter[s1, s2]        -- let A enter receive mode
      test[C, s2, s3] and stutter[s2, s3]        -- let C enter receive mode
      synch[B, C, s3, s4] and carryover[B, C, s3, s4] -- pass from B to C
      leave_receive[C, s4, s5] and stutter[s4, s5] -- C returns to test
      test[C, s5, s6] and release[C, s5, s6]     -- balance C, send to B
      synch[B, A, s6, s7] and carryover[B, A, s6, s7] -- pass from B to A
      leave_send[B, s7, s8] and stutter[s7, s8]  -- B returns to test
  }
}

------------------------------------------------------------------------------

-- fails because it includes a state in I that is unreachable

assert refines {
  example =>
    let s0 = so/first, s = s0.so/next, s' = s.so/next {
        init_I[s0] implies init_S[s0]
        step_I[s, s'] implies step_S[s, s']
      }
}

check refines for 3 Vertex, 3 State

-- a vertex cannot be in test mode and still have carryovers to communicate
pred unreachable [u: Vertex, s: State] {
  u.pc.s = Test
  some v: Vertex | u->v in edges and end[u, v].s = True
}

pred show_unreachable {
  init_I[so/first]
  all s: State - so/last | step_I[s, s.so/next]
  some u: Vertex, s: State | unreachable[u, s]
}

run show_unreachable for 5 Vertex, 30 State

assert refines2 {
  (all x: Vertex, s: State | not unreachable[x, s]) =>
    let s0 = so/first, s = s0.so/next, s' = s.so/next {
        init_I[s0] implies init_S[s0]
        step_I[s, s'] implies step_S[s, s']
      }
}

check refines2 for 10 Vertex, 3 State
