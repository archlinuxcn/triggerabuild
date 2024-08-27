<script>
  import { onMount, createEventDispatcher } from "svelte"
  export let packages
  export let hide_completion
  const dispatch = createEventDispatcher()

  let to
  let input, ul
  let completions = []
  let selected_idx

  onMount(() => {
    const rect = input.getBoundingClientRect()
    ul.style.top = `${rect.height - 1}px`
    ul.style.width = `${rect.width - 2}px`
  });

  function update_list_width() {
    const rect = input.getBoundingClientRect()
    ul.style.width = `${rect.width - 2}px`
  }

  function may_complete() {
    if (to) {
      clearTimeout(to)
    }
    to = setTimeout(function () {
      complete_it()
    }, 100)
  }

  function complete_it() {
    hide_completion = false
    if (!input.value) {
      completions = []
      return
    }
    completions = packages.filter((pkg) => pkg.includes(input.value))
  }

  function select_by_click(e) {
    let el = e.target
    if (el.tagName != "LI") {
      return
    }
    selected_idx = parseInt(el.dataset.idx)
    select_confirmed()
    input.focus()
  }

  function select_by_key(e) {
    if (e.key === "ArrowDown" || (e.key === "n" && e.altKey)) {
      select_next(1)
      e.preventDefault()
    } else if (e.key === "ArrowUp" || (e.key === "p" && e.altKey)) {
      select_next(-1)
      e.preventDefault()
    } else if (e.key === "Enter") {
      select_confirmed()
      e.preventDefault()
    }
  }

  function select_next(dir) {
    if (typeof selected_idx === "number") {
      if (dir > 0) {
        selected_idx = (selected_idx + 1) % completions.length
      } else {
        selected_idx = (selected_idx - 1) % completions.length
      }
    } else {
      if (dir > 0) {
        selected_idx = 0
      } else {
        selected_idx = completions.length - 1
      }
    }
  }

  function select_confirmed() {
    const pkg = completions[selected_idx]
    if (!pkg) {
      return
    }
    dispatch('package', { package: pkg })
  }

</script>

<div>
  <input type="text"
    bind:this={input}
    on:input={may_complete}
    on:keydown={select_by_key}
  />
  <ul
    bind:this={ul}
    on:click={select_by_click}
    on:mousedown|preventDefault={() => {}}
    class:hidden={completions.length === 0 || hide_completion}
    >
    {#each completions as pkg, i (pkg)}
      <li data-idx={i} class:selected={i === selected_idx} title={pkg}>{pkg}</li>
    {/each}
  </ul>
</div>

<svelte:window on:resize={update_list_width} />

<style>
  div {
    position: relative;
  }
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    position: absolute;
    left: 0;
    background-color: white;
    box-shadow: 0 0 4px var(--color-inactive);
    clip-path: polygon(-100% 0, 200% 0, 200% 200%, -100% 200%);
  }
  li {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    cursor: pointer;
    line-height: 2em;
    padding-left: 5px;
    padding-right: 5px;
  }
  ul:not(:hover) > li.selected,
  li:hover {
    background-color: #d9f5ff;
  }
  input {
    padding-left: 5px;
    padding-right: 5px;
    width: min(50em, 100% - 1em);
    box-shadow: 0 0 4px var(--color-inactive);
  }
  input,
  ul {
    border-radius: 0;
    border: 1px solid var(--color-inactive);
  }
  input:focus,
  input:focus ~ ul {
    border-color: var(--color-active);
    box-shadow: 0 0 4px var(--color-active);
    outline: 1px solid var(--color-active);
  }
  input:focus ~ ul {
    border-top-color: var(--color-inactive);
  }

  .hidden {
    display: none;
  }
</style>
