<script>
  import { onMount } from "svelte";
  import PackageInput from "./PackageInput.svelte";
  import Removable from "./Removable.svelte";

  let info
  let to_build = []
  let packages = []
  let submit_btn
  let hide_completion = false
  let error = ''

  onMount(async () => {
    const res = await fetch('info')
    const j = await res.json()
    info = j.data
    if(info.username){
      const res = await fetch('pkglist')
      const j = await res.json()
      packages = j.data
    }
  })

  function add_package(e) {
    const pkg = e.detail.package
    if(!to_build.includes(pkg)) {
      to_build[to_build.length] = pkg
    }
  }

  function remove_package(e) {
    const pkg = e.detail.label
    to_build = to_build.filter((p) => p != pkg)
  }

  async function submit_build() {
    submit_btn.textContent = "提交中..."
    submit_btn.disabled = true
    hide_completion = true
    error = ''
    const res = await fetch('submit', {
      method: 'POST',
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(to_build),
    })
    try{
      if(res.ok) {
        const j = await res.json()
        location.reload()
      } else {
        throw res.statusText
      }
    }catch(e){
      error = e
      submit_btn.textContent = "提交构建"
      submit_btn.disabled = false
    }
  }
</script>

<main>
{#if info}
  {#if info.lilac == "running"}
    <p>lilac 正在运行（<a href="/~imlonghao/current/">查看状态</a>）。</p>
  {:else if info.lilac == "conflict"}
    <p>lilac 因为 git 仓库而无法运行，请等待手动处理。</p>
  {:else if info.lilac == "sleeping"}
    <p>lilac 未在运行。</p>
  {:else}
    <p>lilac 状况不明，请呼叫管理员。</p>
  {/if}
  {#if info.queued.length > 0}
    <p>等待队列：{info.queued.join(", ")}。</p>
  {/if}
  {#if info.username}
    <p>
      新增要构建的包：
      {#each to_build as pkg}<Removable label={pkg} on:remove={remove_package}/>{/each}
      <button bind:this={submit_btn} on:click|preventDefault={submit_build} disabled={to_build.length === 0}>提交构建</button>
    </p>
    <PackageInput {packages} bind:hide_completion on:package={add_package} />
  {:else}
    <p>使用 <a href="login">GitHub 登录</a>以新增要构建的包。</p>
  {/if}
  {#if error}
    <p class="error">{error}</p>
  {/if}
{:else}
  加载中...
{/if}
</main>

<style>
  .error {
    color: red;
  }

  :global(input),
  :global(button) {
    border-radius: 0;
    border: 1px solid var(--color-inactive);
    height: 2.3em;
  }
  :global(input:focus),
  :global(button:focus) {
    border-color: var(--color-active);
    outline: 1px solid var(--color-active);
    /* make focus border topmost */
    z-index: 10;
  }
  :global(:root) {
    --color-inactive: #bfbfbf;
    --color-active: #add8e6;
  }
</style>
