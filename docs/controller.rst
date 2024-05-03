.. _controller:

Controller
==========

.. * unit
..     * dynamically imported python module with info descriptor
..     * single instance of single unit definition
..         * unit name is predefined as part of unit definition
..           (possible naming collisions)
..     * can be implemented as part of hat-controller or in other repositories
..     * instance lifetime is bound to controller lifetime
..         * unit is created when controller is active and closed when controller
..           is deactivated (usually by starting process or by monitor blessing)
..         * "internal" closing of unit closes controller - unit can control
..           controller lifetime
..     * unit defines set of provided functions
..         * function names are made of arbitrary number of string segments
..           delimited by ``.``
..             * api mapping to nested js objects
..         * function arguments and return value must be json serializable data
..         * functions are called during action execution
.. * environment
..     * single interpreter instance with single global context
..     * multiple environments can be configured
..     * each environment has it's own execution thread independent of other
..       environments
.. * action
..     * js code bound to specific environment
..     * associated with trigger subscription
..         * when trigger occurs, action is executed
..     * action is executed as body of anonymous function defined inside global
..       scope
..     * initial action
..         * specific action executed immediately after unit initialization
..         * executed as part of global scope
..         * trigger is not defined
.. * trigger
..     * identified by type and name
..         * both type and names have segments delimited by ``/``
..           (character ``/`` is not supported as part of type/name segment)
..     * based on trigger type, each unit defines triggers with additional trigger
..       data
..     * triggers are shared between environments
..         * triggers raised by action of one environment is propagated to
..           all environments
..         * trigger data must be json serializable
..     * in case of trigger subscriptions, ``*`` can replace zero or more
..       type/name segments
..         * can occur only at the end of type/name

.. * todo
..     * should we allow multiple instances of same unit?
..         * in that case unit name is part of configuration and
..           ts api definition can't be bound to predefined name
..         * name clashing is not problematic
