<template>
  <div id="app">
    <div id="columns-container">

      <b-card title="Arknights Auto Helper" :sub-title="version" class="status-card">
        <b-input-group class="mt-3">
          <b-input-group-prepend is-text>
            <b-icon icon="plug-fill" />设备
          </b-input-group-prepend>
          <b-input-group-append class="flex-grow-1">
            <b-dropdown :text="deviceName" right class="flex-grow-1">
              <b-dropdown-item disabled><b>可用设备</b></b-dropdown-item>
              <b-dropdown-item v-for="dev in availiableDevices" v-bind:key="dev" @click="connectDevice(dev)">{{dev}}</b-dropdown-item>
              <b-dropdown-divider/>
              <b-dropdown-item v-b-modal.connect-device>连接设备</b-dropdown-item>
            </b-dropdown>
          </b-input-group-append>
        </b-input-group>

        <div class="mt-3">任务队列
          <div class="float-right">
              <b-button size="sm" variant="outline-danger" v-b-tooltip.hover title="移除选中项" :disabled="selectedPendingJob.length == 0" @click="dequeueSelectedJobs"><b-icon-trash/></b-button>
          </div>
        </div>
        <b-form-select class="mt-1" v-model="selectedPendingJob" :options="pendingJobs" multiple :select-size="8"></b-form-select>
        <b-button block class="mt-1" size="sm"
          :variant="canPauseJob ? 'warning' : 'success'"
          :disabled="!(canPauseJob || canResumeJobQueue)"
          @click="toggleQueueState"
          ><b-icon 
          :icon="canPauseJob ? 'pause-fill' : 'play-fill'"
          />{{canPauseJob ? '暂停' : (appRunning ? '继续' : '启动')}}队列</b-button>
          <div class="mt-3">运行状态</div>
          <b-input-group>
            <b-input-group-prepend is-text>
              <b-icon icon="arrow-right"/>
            </b-input-group-prepend>
            <b-form-input readonly :value="currentJobTitle"></b-form-input>
          </b-input-group>
          <b-input-group class="mt-1">
            <b-input-group-prepend is-text>
              <b-icon icon="pause-circle" v-show="!appRunning"/>
              <b-icon icon="stopwatch" v-show="appRunning && workerWaiting"/>
              <b-spinner small v-show="appRunning && !workerWaiting"/>
            </b-input-group-prepend>
              <b-form-input readonly :value="timerText"></b-form-input>
            <b-input-group-append>
              <b-button variant="info" v-b-tooltip.hover title="跳过当前等待时间" :disabled="!(appRunning && workerWaiting && allowSkipWait)" @click="sendAction('skip_wait')"><b-icon-skip-forward-fill/></b-button>
              <b-button variant="outline-danger" v-b-tooltip.hover title="停止助手" :disabled="!appRunning" @click="sendAction('interrupt')"><b-icon-x-octagon size="sm"/></b-button>
            </b-input-group-append>
          </b-input-group>
          <button @click="onWorkerIdle">complete current job</button>
        <b-form-checkbox v-model="appRunning">app running</b-form-checkbox>
        <b-form-checkbox v-model="workerWaiting">worker waiting</b-form-checkbox>
        <b-form-checkbox v-model="allowSkipWait">allow skip wait</b-form-checkbox>
      </b-card>

      <div id="action-cards">
        <b-card title="快速启动" class="action-card">
          <b-form class="mt-3">
            <b-form-group label="关卡" label-for="navigate-option" label-cols="2" >
              <b-form-radio-group id="navigate-option" v-model="onStage" buttons button-variant="outline-secondary" size="sm">
                <b-form-radio value="current">当前关卡</b-form-radio>
                <b-form-radio value="navigate">指定关卡</b-form-radio>
                <b-button v-if="onStage == 'navigate'" variant="outline-secondary" v-b-modal.choose-stage>{{choosedStage}}</b-button>
              </b-form-radio-group>
            </b-form-group>
              <b-form-group label="次数" label-for="repeat-count" label-cols="2" >
                <div class="d-flex flex-row align-items-center">
                  <b-form-input id="repeat-count" v-model="repeatCount" min="0" max="9999" type="number" style="width: 6em"></b-form-input>
                  <b-button-group size="sm" class="ml-2">
                    <b-button variant="outline-secondary" @click="repeatCount=1">1</b-button>
                    <b-button variant="outline-secondary" @click="repeatCount--" :disabled="repeatCount==0"><b-icon-dash/></b-button>
                    <b-button variant="outline-secondary" @click="repeatCount++"><b-icon-plus/></b-button>
                    <b-button variant="outline-secondary" @click="repeatCount=9999">∞</b-button>
                  </b-button-group>
                </div>
              </b-form-group>
              <b-form-checkbox v-model="refillWithItem" name="" switch>使用道具回复体力</b-form-checkbox>
              <b-form-checkbox v-model="refillWithOriginium" name="" switch class="mt-1">使用源石回复体力</b-form-checkbox>
          </b-form>
          <template #footer>
            <div class="clearfix">
              <b-button-group class="float-right">
                <b-button :disabled="appRunning" @click="goJob(getQuickStartJob())">Go</b-button>
                <b-button variant="outline-secondary" @click="enqueueJob(getQuickStartJob())">Enqueue</b-button>
              </b-button-group>
            </div>
          </template>
        </b-card>

        <b-card title="领取任务奖励" class="action-card">
          <template #footer>
            <div class="clearfix">
              <b-button-group class="float-right">
                <b-button :disabled="appRunning" @click="goJob(getCollectJob())">Go</b-button>
                <b-button variant="outline-secondary" @click="enqueueJob(getCollectJob())">Enqueue</b-button>
              </b-button-group>
            </div>
          </template>
        </b-card>

        <b-card title="公开招募计算" class="action-card">
          <template #footer>
            <div class="clearfix">
              <b-button :disabled="appRunning" class="float-right" @click="recruit">Go</b-button>
            </div>
          </template>
        </b-card>
      </div>

      <b-card header="战利品" class="status-card"></b-card>

    </div>

    <div class="log-console bg-dark text-light">
      <div id="detailed-console" v-show="consoleExpanded" ref="consoleContainer"></div>
      <div id="status-line">
        <b-button size="sm" squared @click="toggleConsole"><b-icon :icon="consoleExpanded ? 'chevron-bar-down' : 'chevron-bar-up'"/></b-button><div id="last-console-line" class="ml-2"><span class="align-middle">{{lastConsoleLine}}</span></div></div>
      </div>
  <b-modal id="connect-device" title="连接设备">
    TODO 协议: adb
    <b-form-input ref="connectDeviceInput"></b-form-input>
  </b-modal>

  <b-modal id="choose-stage" title="选择关卡" @show="chooseStageShown" @ok="chooseStageConfirm">
    TODO
    <b-form-input v-model.lazy="newChoosedStage"></b-form-input>
  </b-modal>

  </div>
</template>

<script>
import Vue from 'vue'
import Component from 'vue-class-component'
import { IconsPlugin } from 'bootstrap-vue'

// Vue.use(BootstrapVue)
Vue.use(IconsPlugin)

function isVisible(domElement, root=null) {
  return new Promise(resolve => {
    const o = new IntersectionObserver(([entry]) => {
    resolve(entry.intersectionRatio === 1);
    o.disconnect();
    }, {root: root});
    o.observe(domElement);
  });
}


@Component
export default class App extends Vue {
  show = true
  version = 'loading'
  deviceName = '(auto)'
  availiableDevices = ['adb:127.0.0.1:5555', 'adb:127.0.0.1:7555']
  onStage = 'current'
  choosedStage = '1-7'
  newChoosedStage = ''
  repeatCount = 9999
  appRunning = false
  timerText = "114/514"
  workerWaiting = true
  allowSkipWait = true
  runQueuedJobs = false
  refillWithItem = false
  refillWithOriginium = false
  selectedPendingJob = []
  consoleExpanded = false
  lastConsoleLine = "shit"
  currentJobTitle = "空闲"
  pendingJobs = []

  get canResumeJobQueue() {
    return this.pendingJobs.length > 0 && (!this.runQueuedJobs || !this.appRunning)
  }

  get canPauseJob() {
    return this.appRunning && this.pendingJobs.length > 0 && this.runQueuedJobs
  }

  mounted() {
    this.lastelm = null
    this.currentWaitInterval = null
    this.pendingCalls = new Map()
    // this.intervals.push(setInterval(()=>{
    //   this.addConsoleLine("fuck   ! @" + new Date());
    // }, 500))

    // this.intervals.push(setInterval(()=>{
    //     this.addConsoleLine("shit  ! @" + new Date(), "warn");
    // }, 1000))

    // this.intervals.push(setInterval(()=>{
        this.addConsoleLine("fucking loooooooooooooooooooooooooooooooooooooooooooooooooong   shit  ! @" + new Date(), "error");
    // }, 5000))

    let sock = new WebSocket(location.href)
    this.callSequence = 0
    this.ws = sock
    let token = new URL(location.href).searchParams.get('auth')
    sock.addEventListener("open", ()=>{
      this.sendAction("authorize", [token])
    })
  }

  beforeDestroy() {
    this.intervals.forEach(x => clearInterval(x));
  }

  addConsoleLine (text, level="info") {
    this.lastConsoleLine = text.split("\n").pop()
    let newelm = document.createElement("p")
    newelm.innerText = text
    newelm.classList.add("log-" + level)
    let consoleContainer = this.$refs.consoleContainer
    consoleContainer.appendChild(newelm)
    if (consoleContainer.childElementCount > 1000) {
        consoleContainer.firstElementChild.remove()
    }
    if (this.lastelm) {
      isVisible(this.lastelm, consoleContainer).then(visible => {
        if (visible) {
          console.log("last line visible")
          consoleContainer.scrollTop = newelm.offsetTop
        } else {
          console.log("last line invisible")
        }
      })
    }
    this.lastelm = newelm
  }

  scrollConsoleToLast() {
    this.$nextTick(()=>{
      this.$refs.consoleContainer.lastElementChild.scrollIntoView()
    })
  }

  toggleConsole() {
    console.log('Toggle button clicked')
    this.consoleExpanded = !this.consoleExpanded
    if (this.consoleExpanded) {
      this.scrollConsoleToLast()
    }
  }

  connecrDevice(dev) {
    this.sendAction("connect", dev)
  }

  getQuickStartJob() {
    let result = {value: "Job@"+(+new Date()), text: "", action: []}
    let stageText = this.onStage === 'current' ? '当前关卡' : '['+this.choosedStage+']'
    let count = this.repeatCount
    let title = stageText + '×' + count
    if (this.refillWithItem) title += " 使用道具"
    if (this.refillWithOriginium) title += " 使用源石"
    result.text = title
    result.action.push({name: "set_refill_with_item", args: [this.refillWithItem]})
    result.action.push({name: "set_refill_with_originium", args: [this.refillWithOriginium]})
    if (this.onStage === 'current') {
      result.action.push({name: "module_battle_slim", args: [count]})
    } else {
      result.action.push({name: "module_battle", args: [this.choosedStage, count]})
    }
    console.log(result)
    return result
  }

  getCollectJob() {
    return {value: "Job@"+(+new Date()), text: "领取任务奖励", action: [{name: "clear_task", args: []}]}
  }

  goJob(job) {
    this.appRunning = true
    this.currentJobTitle = job.text
    for(let action of job.action) {
      this.sendAction(action.name, action.args)
    }
  }

  sendAction(action, args=[]) {
    console.log("sending action", action, "with args", args)
    this.ws.send(JSON.stringify({action, args}))
  }

  callRemote(action, args=[]) {
    console.log("calling", action, "with args", args)
    let tag = "Call#"+this.callSequence+"@"+(+new Date())
    this.ws.send(JSON.stringify({action, args, tag}))
    return new Promise((resolve, reject) => {
      this.pendingCalls.set(tag, {resolve, reject})
    })
  }

  enqueueJob(job) {
    let oldQD = this.pendingJobs.length
    this.pendingJobs.push(job)
    if (oldQD === 0) {
      this.runQueuedJobs = true
    }
  }

  dequeueSelectedJobs() {
    console.log(this.selectedPendingJob)
    for(let id of this.selectedPendingJob) {
      let removedjobs = this.pendingJobs.splice(this.pendingJobs.findIndex(v=>v.value === id), 1)
      console.log(removedjobs)
    }
  }

  toggleQueueState() {
    if(this.appRunning) {
      this.runQueuedJobs = !this.runQueuedJobs
    } else {
      this.runNextJobInQueue()
    }
  }

  runNextJobInQueue() {
    if (this.pendingJobs.length > 0) {
      this.goJob(this.pendingJobs.shift())
      this.runQueuedJobs = true
    } else {
      this.setAppIdle()
    }
  }

  setAppIdle() {
    this.appRunning = false
    this.currentJobTitle = '空闲'
  }

  onReceived(obj) {
    switch (obj.type) {
      case "update-value":
        this.onUpdateValue(obj.name, obj.value)
        break
      case "idle":
        this.onWorkerIdle()
        break
      case "update-wait":
        this.onWait(obj.duration, obj.allow_skip)
        break
      case "authorized":
        this.onAuthorized()
        break
      case "log":
        this.addConsoleLine(obj.text, obj.level)
        break
      case "call-result":
        this.onCallResult(obj)
        break
      default:
        break;
    }
  }

  onWorkerIdle() {
    if (this.runQueuedJobs) {
      this.runNextJobInQueue()
    } else {
      this.setAppIdle()
    }
  }

  onWait(duration, allowSkip) {
    if (this.currentWaitInterval !== null) {
      clearInterval(this.currentWaitInterval)
    }
    if (duration == 0) {
      this.workerWaiting = false
      this.timerText = ""
      return
    }
    this.workerWaiting = true
    this.allowSkipWait = allowSkip
    let startTime = +new Date() / 1000
    // let endTime = startTime + duration
    this.timerText = "0/" + duration.toFixed(0)
    this.currentWaitInterval = setInterval(()=>{
      let now = +new Date() / 1000
      let elapsed = now - startTime
      this.timerText = elapsed.toFixed(0) + "/" + duration.toFixed(0)
      if (elapsed >= duration) {
        clearInterval(this.currentWaitInterval)
      }
    }, 1000)
  }

  onUpdateValue(name, value) {
    console.log("update value", name, "=", value)
    switch (name) {
      case "web:current-device":
        this.deviceName = value.toString()
        break
      case "web:availiable-devices":
        this.availiableDevices = value
        break
      case 'web:version':
        this.version = value.toString()
        break
      default:
        break
    }
  }

  onCallResult(obj) {
    let tag = obj.tag
    let callrecord = this.pendingCalls.get(tag)
    if (Object.prototype.hasOwnProperty.call(callrecord, "resolve")) {
      return
    }
    if (obj.status == "resolved") {
      callrecord.resolve(obj.return_value)
    } else {
      let exc = obj.exception
      let err = new Error(exc.message)
      err.stack = exc.trace
      callrecord.reject(err)
    }
  }

  recruit() {
    1
  }

  chooseStageShown() {
    this.newChoosedStage = this.choosedStage
  }

  chooseStageConfirm() {
    this.choosedStage = this.newChoosedStage
  }

}
</script>

<style>


html, body {
  height: 100%;
}

#app {
  display: flex;
  flex-direction: column;
  padding-bottom: 4rem;
  min-height: 100%;
  align-content: flex-start;
}

#columns-container {
  flex-grow: 1;
  
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  align-content: flex-start;
  flex-wrap: wrap;
}

.action-card {
  max-width: 40rem;
  min-width: 20rem;
  margin: 0.5rem 0.25rem;
  /* flex: 114514; */
}

.status-card {
  min-width: 20rem;
  max-width: 20rem;
  margin: 0.5rem 0.25rem;
  flex-grow: 1;
  min-height: 10rem;
}

#action-cards {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: flex-start;
  flex: 114514;
  align-content: flex-start;
}

.log-console {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  box-shadow: 0 0 1rem rgba(0, 0, 0, 0.375);
}

#detailed-console {
  background-color: #1d1f21;
  color: #c5c8c6;
  font-family: monospace;
  height: 16em;
  overflow-y: scroll;
}

#status-line {
  display: flex;
  flex-direction: row;
  align-items: center;
  align-content: center;
  justify-content: center;
}

#last-console-line {
  white-space: pre;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-grow: 1;
}

#detailed-console p {
    margin: 0;
    line-height: 1em;
    white-space: pre-wrap;
}

#detailed-console .log-error {
    color: #cc6666;
}

#detailed-console .log-warn {
    color: #f0c674;
}

</style>
