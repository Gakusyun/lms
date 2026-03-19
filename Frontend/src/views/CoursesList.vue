<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import GenericList from '../components/GenericList.vue'
import GenericCreateModal from '../components/GenericCreateModal.vue'

const router = useRouter()

// 获取当前用户角色
const currentUserRole = computed(() => localStorage.getItem('role') || '')
const isAdmin = computed(() => currentUserRole.value === 'admin')

// 跳转到课程学生名单页面
const goToCourseStudents = (courseId: number) => {
  router.push(`/courses/${courseId}/students`)
}


</script>

<template>
  <div>
    <GenericList
      endpoint="/courses"
      title="课程列表"
      :show-actions="currentUserRole !== 'student'"
      :columns="[
        { key: 'course_id', label: '课程ID' },
        { key: 'course_name', label: '课程名称' },
        { key: 'class_hours', label: '课时' },
        { key: 'teacher_name', label: '教师姓名' },
        {
          key: 'enrollment_count',
          label: '选课人数',
          formatter: (value: any) => `${value || 0} 人`
        }
      ]"
      item-label="门课程"
      :show-create="isAdmin"
      create-type="course"
    >
      <template #actions="{ item }">
        <button @click="goToCourseStudents(item.course_id)" class="btn btn-primary btn-sm">
          查看学生名单
        </button>
      </template>
    </GenericList>
  </div>
</template>

