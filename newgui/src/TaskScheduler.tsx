import { Flex, Box } from '@chakra-ui/layout'
import React, { useMemo } from 'react';
import { createPortal } from 'react-dom';
import { Button, ButtonGroup, Card, Divider, Icon, Text } from '@blueprintjs/core';
import { Tooltip2 } from '@blueprintjs/popover2';
import * as DnD from '@dnd-kit/core';
import * as DnDSortable from '@dnd-kit/sortable';
import { restrictToVerticalAxis } from '@dnd-kit/modifiers';
import { CSS } from '@dnd-kit/utilities';

import "./TaskScheduler.scss";

import { currentTab } from './AppGlobalState';

enum TaskItemStatus {
  Completed,
  Running,
  Failed,
  Pending,
  Skip,
  Stop,
}

interface TaskItemData {
  id: string;
  title: string;
  configComponent?: React.Component;
  configState?: any;
}

interface IDispatcherTaskItemData extends TaskItemData {
  itemStatus: TaskItemStatus;
}

interface ITaskItemRenderData extends IDispatcherTaskItemData {
  checked?: boolean;
  dragging?: boolean;
  overlay?: boolean;
}

interface ITaskItemUIEvents {
  onCheckedChange: (id: string, clickedOnCheckbox: boolean) => void;
  onDisableChange: (id: string) => void;
  onConfig: (id: string) => void;
  changeDisplayOrder: (id: string, newIndex: number) => void;
  onDragStart: () => void;
  onDragEnd: (accept: boolean) => void;
}

interface ITaskItemProps extends ITaskItemRenderData, ITaskItemUIEvents {
  index: number;
  dragHandleProps?: any;
  style?: React.CSSProperties;
}

const TaskItem = React.forwardRef((props: ITaskItemProps, ref) => {
  const listDragging = props.dragging
  const { id, itemStatus, title, checked, onConfig, onCheckedChange, onDisableChange } = props;

  const checkbox = useMemo(() => {
    const icon = checked ? "tick-circle" : "circle";
    return <Button className="item-checkbox" icon={icon} minimal small onClick={(e) => { onCheckedChange(id, true); e.stopPropagation(); }} />;
  }, [checked, onCheckedChange, id]);


  const statusIcon = useMemo(() => {
    const commonProps = { size: 16, tagName: 'div' as any, onClick: (e) => { onDisableChange(id); e.stopPropagation(); } };
    let text, icon, intent = null;
    switch (itemStatus) {
      case TaskItemStatus.Completed:
        text = '已完成';
        icon = 'tick';
        intent = 'success';
        break;
      case TaskItemStatus.Failed:
        text = '错误';
        icon = 'error';
        intent = 'danger';
        break;
      case TaskItemStatus.Running:
        text = '正在运行';
        icon = 'arrow-right';
        intent = 'primary';
        break;
      case TaskItemStatus.Pending:
        text = '待运行';
        icon = 'time';
        break;
      case TaskItemStatus.Skip:
        text = '跳过';
        icon = 'double-chevron-down';
        break;
      case TaskItemStatus.Stop:
        text = '在此停止队列';
        icon = 'ban-circle';
        intent = 'warning';
        break;
    }
    return <Tooltip2 minimal placement='top' content={text} className='task-item-icon'><Button minimal small icon={icon} {...commonProps} intent={intent} /></Tooltip2>;
  }, [itemStatus, id, onDisableChange]);

  const controls = useMemo(() => {
    return (
      <Box className="item-controls">
        <Button icon="cog" minimal small onClick={(e) => { onConfig(id); e.stopPropagation() }} />
      </Box>
    );
  }, [id, onConfig]);


  const textElm = useMemo(() => {
    const muted = itemStatus === TaskItemStatus.Skip || itemStatus === TaskItemStatus.Stop;
    return <Text ellipsize={true} className={"task-item-title flex-grow-1" + (muted ? ' bp3-text-muted' : '')}>{title}</Text>
  }, [itemStatus, title]);

  let classes = ['task-item'];
  if (props.checked) classes.push('selected');
  if (!listDragging) classes.push('hover-effect');
  if (props.dragging) classes.push('dragging');
  if (props.overlay) classes.push('overlay');
  return (
    <Box ref={ref as any} className={classes.join(' ')} style={props.style}
      onClick={e => props.onCheckedChange(props.id, false)}>
      <Box pl="0px" pr="10px" py="5px" h="100%" >
        <Flex flexDirection="row" alignItems="center" h="100%">
          <Box {...props.dragHandleProps}><Icon icon="drag-handle-vertical" size={16} className="drag-handle" tagName="div" /></Box>
          {checkbox}
          {statusIcon}
          {textElm}
          {controls}
        </Flex>
      </Box>
      <Divider />
      {props.overlay ? <Box className="task-item-mask" /> : null}
    </Box>
  );
});


const SortableTaskItem = (props: ITaskItemProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = DnDSortable.useSortable({ id: props.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };


  let newStyle = { ...props.style, ...style };
  let newProps = { ...props, style: newStyle };
  return <TaskItem ref={setNodeRef} {...newProps} {...attributes} dragHandleProps={listeners} />;
}


interface ITaskListProps extends ITaskItemUIEvents {
  tasks: ITaskItemRenderData[];
  style: React.CSSProperties;
  dragging?: boolean;
  onSelectAllToggled: () => void;
  onDeselect: () => void;
  onResetTask: () => void;
  onDeleteTask: () => void;
}

const TaskList: React.FunctionComponent<ITaskListProps> = function (props) {

  const sensors = DnD.useSensors(
    DnD.useSensor(DnD.PointerSensor),
    DnD.useSensor(DnD.KeyboardSensor, {
      coordinateGetter: DnDSortable.sortableKeyboardCoordinates,
    })
  );

  const [draggingId, setDraggingId] = React.useState<string | null>(null);

  const handleDragStart = (event) => {
    const { active } = event;
    console.log('drag start', active.id);
    setDraggingId(active.id);
  }

  const handleDragEnd = (event) => {
    const { active, over } = event;
    setDraggingId(null);

    if (active.id !== over.id) {
      console.log('drag end', active.id, over.id);
      // setItems((items) => {
      //   const oldIndex = items.indexOf(active.id);
      //   const newIndex = items.indexOf(over.id);

      //   return arrayMove(items, oldIndex, newIndex);
      // });
    }
  };

  let hasChecked = false, allChecked = true;
  let overlayElt = null;
  let items = []
  const dropAnimation = {
    duration: 250,
    easing: 'cubic-bezier(0.18, 0.67, 0.6, 1.22)',
  };
  props.tasks.forEach((task, index) => {
    hasChecked = hasChecked || task.checked;
    allChecked = allChecked && task.checked;
    const dragging = draggingId === task.id;
    const propsWithoutStyle = { ...props, style: null };
    if (dragging) {
      overlayElt = <div className="default-background opacity-80"><TaskItem key={task.id} index={index} {...task} {...propsWithoutStyle} overlay /></div>;
    }
    items.push(<SortableTaskItem key={task.id} index={index} {...task} {...propsWithoutStyle} dragging={dragging} />);
  });

  return (
    <DnD.DndContext sensors={sensors} collisionDetection={DnD.closestCenter} modifiers={[restrictToVerticalAxis]} onDragEnd={handleDragEnd} onDragStart={handleDragStart}>
      <Card style={{ ...props.style, padding: "0", flexGrow: 1 }} className='tasklist-widget default-background' >
        <Flex position="relative" w="100%" h="100%" flexDirection="column" className='scroller overflow-y-scroll'>
          <DnDSortable.SortableContext items={props.tasks} strategy={DnDSortable.verticalListSortingStrategy}  >

            {items}
          </DnDSortable.SortableContext>
          <Button minimal large fill icon="plus" onClick={() => currentTab.setValue('gallery')}>前往任务库</Button>
          <Box className="grower" />
          {hasChecked ?
            <Box position='sticky' bottom={0}>
              <ButtonGroup fill className="task-list-toolbar">
                <Button outlined small icon={allChecked ? 'circle' : 'tick-circle'} text={allChecked ? '取消' : '全选'} onClick={(e) => props.onSelectAllToggled()} />
                <Button outlined small icon="refresh" intent="success" text="重置" onClick={(e) => props.onResetTask()} />
                <Button outlined small icon="trash" intent="danger" text="删除" onClick={(e) => props.onDeleteTask()} />
                <Button outlined small icon="cross" onClick={(e) => props.onDeselect()} />
              </ButtonGroup>
            </Box>
            : <Box className='toolbar-placeholder' />}
        </Flex>
      </Card>

      {createPortal(
        <DnD.DragOverlay dropAnimation={dropAnimation}>
          {draggingId !== null ? overlayElt : null}
        </DnD.DragOverlay>, document.body)}

    </DnD.DndContext>

  );
}


export default class TaskScheduler extends React.Component {
  state: { dispatcherState: string, workerState: string, tasks: ITaskItemRenderData[], draggingTasks?: ITaskItemRenderData[], draggingId?: string }

  constructor(props: any) {
    super(props);
    this.state = {
      dispatcherState: 'running',
      workerState: 'running',
      tasks: [
        { id: '111', title: '当前关卡×114', itemStatus: TaskItemStatus.Completed, checked: false },
        { id: '222', title: '当前关卡×514', itemStatus: TaskItemStatus.Failed, checked: false },
        { id: '333', title: '当前关卡×1919810893931', itemStatus: TaskItemStatus.Running, checked: false },
        { id: '444', title: '当前关卡×810', itemStatus: TaskItemStatus.Skip, checked: false },
        { id: '555', title: '当前关卡×893', itemStatus: TaskItemStatus.Pending, checked: false },
      ],
      draggingTasks: null,
      draggingId: null,
    };
  }

  handleCheckedChange = (id: string, clickedOnCheckbox: boolean) => {
    console.log("checked change: " + id + " " + clickedOnCheckbox);
    let index = this.state.tasks.findIndex(t => t.id === id);
    let changed = false;
    if (index >= 0) {
      let tasks = this.state.tasks.slice();
      let task = tasks[index];
      if (clickedOnCheckbox) {
        // explicitly select a task
        task.checked = !task.checked;
        changed = true;
      } else {
        // clicked on background
        // 1. move current selection if selected another task
        // 2. deselect self if self is the only selected task
        let selectedCount = tasks.filter(t => t.checked).length;
        if (selectedCount === 0 || selectedCount === 1) {
          if (task.checked) {
            task.checked = false;
            changed = true;
          } else {
            // another task is selected, move selecton to this task
            tasks.forEach(t => t.checked = false);
            task.checked = true;
            changed = true;
          }
        }
      }
      if (changed) {
        this.setState({ tasks: tasks });
      }
    }
  };

  handleDisableChange = (id: string) => {
    console.log("disable change: " + id);
    let index = this.state.tasks.findIndex(t => t.id === id);
    let changed = false;
    if (index >= 0) {
      let tasks = this.state.tasks.slice();
      let task = tasks[index];
      switch (task.itemStatus) {
        case TaskItemStatus.Completed:
        case TaskItemStatus.Failed:
          task.itemStatus = TaskItemStatus.Pending;
          changed = true;
          break;
        case TaskItemStatus.Pending:
          task.itemStatus = TaskItemStatus.Skip;
          changed = true;
          break;
        case TaskItemStatus.Skip:
          task.itemStatus = TaskItemStatus.Stop;
          changed = true;
          break;
        case TaskItemStatus.Stop:
          task.itemStatus = TaskItemStatus.Pending;
          changed = true;
          break;
        default:
          break;
      }
      if (changed) {
        this.setState({ tasks: tasks });
      }
    }
  };

  handleSelectAllToggled = () => {
    console.log("select all toggled");
    let tasks = this.state.tasks.slice();
    let allChecked = tasks.every(t => t.checked);
    if (allChecked) {
      tasks.forEach(t => t.checked = false);
    } else {
      tasks.forEach(t => t.checked = true);
    }
    this.setState({ tasks: tasks });
  };

  handleDeselectAll = () => {
    console.log("deselect all");
    let tasks = this.state.tasks.slice();
    tasks.forEach(t => t.checked = false);
    this.setState({ tasks: tasks });
  };

  handleChangeDisplayOrder = (id: string, newIndex: number) => {
    console.log("change display order: " + id + " " + newIndex);
    let tasks = this.state.draggingTasks === null ? this.state.tasks.slice() : this.state.draggingTasks.slice();
    let index = tasks.findIndex(t => t.id === id);
    if (index >= 0) {
      let [task] = tasks.splice(index, 1);
      tasks.splice(newIndex, 0, task);
      this.setState({ draggingTasks: tasks });
    }
  };

  handleDragEnd = (accept: boolean) => {
    console.log("drag end: " + accept);
    if (accept && this.state.draggingTasks !== null) {
      this.setState({ tasks: this.state.draggingTasks, draggingTasks: null });
    } else {
      this.setState({ draggingTasks: null });
    }
    return true;
  };

  dummy = () => { };

  render() {
    return (
      <Flex flexDirection="column" flexGrow={1} gap={8}>
        <ButtonGroup large>
          {this.state.dispatcherState === 'stopped' ?
            <Button icon="play" text="开始队列" fill intent='success' /> :
            <Button outlined icon="stopwatch" text="114/514" fill intent='warning' />
          }
          <Button icon="stop" intent='danger' disabled={this.state.dispatcherState !== 'running'} />
        </ButtonGroup>

        <TaskList style={{ flexGrow: 1, flexShrink: 1, height: "0" }}
          tasks={this.state.draggingTasks === null ? this.state.tasks : this.state.draggingTasks}
          onCheckedChange={this.handleCheckedChange}
          onConfig={this.dummy}
          onDisableChange={this.handleDisableChange}
          onSelectAllToggled={this.handleSelectAllToggled}
          onDeleteTask={this.dummy}
          onResetTask={this.dummy}
          onDeselect={this.handleDeselectAll}
          changeDisplayOrder={this.handleChangeDisplayOrder}
          onDragStart={this.dummy}
          onDragEnd={this.handleDragEnd}
          dragging={this.state.draggingTasks !== null}
        />

        <Flex flexDirection="row" justifyContent="space-between">
          <ButtonGroup>
            <Tooltip2 minimal placement='top' content="保存当前队列供以后使用"><Button icon="floppy-disk" text="保存" /></Tooltip2>
            <Tooltip2 minimal placement='top' content="载入保存的队列"><Button icon="document-open" text="载入" /></Tooltip2>
          </ButtonGroup>
        </Flex>
      </Flex>
    )
  }
}
