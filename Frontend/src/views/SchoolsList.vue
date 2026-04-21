<script setup lang="ts">
import GenericList from '../components/GenericList.vue'
</script>

<template>
  <div>
    <GenericList
      endpoint="/schools"
      title="学院列表"
      :columns="[
        { key: 'school_id', label: '学院ID' },
        { key: 'school_name', label: '学院名称' }
      ]"
      item-label="个学院"
      :show-actions="false"
      :show-create="false"
      hide-export
    />
  </div>
</template>
