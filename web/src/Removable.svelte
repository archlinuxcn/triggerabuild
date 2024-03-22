<script>
  import { createEventDispatcher } from "svelte"
  export let label
  const dispatch = createEventDispatcher()

  function remove_package(e) {
    dispatch('remove', { label: label })
  }

</script>

<span>{label}<sup><a href="javascript:void(0)" on:click|preventDefault={remove_package}>x</a></sup></span>

<style>
  span {
    padding-right: 2px;
  }
  a {
    text-decoration: none;
    padding: 2px;
  }
</style>
