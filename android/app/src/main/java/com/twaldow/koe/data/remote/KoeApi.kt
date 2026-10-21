package com.twaldow.koe.data.remote

import com.twaldow.koe.data.remote.dto.FolderCreateRequest
import com.twaldow.koe.data.remote.dto.FolderDto
import com.twaldow.koe.data.remote.dto.FolderUpdateRequest
import com.twaldow.koe.data.remote.dto.TodoCreateRequest
import com.twaldow.koe.data.remote.dto.TodoDto
import com.twaldow.koe.data.remote.dto.TodoUpdateRequest
import com.twaldow.koe.data.remote.dto.VoiceRequest
import com.twaldow.koe.data.remote.dto.VoiceResponse
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface KoeApi {

    @GET("folders")
    suspend fun getFolders(): List<FolderDto>

    @POST("folders")
    suspend fun createFolder(@Body body: FolderCreateRequest): FolderDto

    @PATCH("folders/{id}")
    suspend fun updateFolder(@Path("id") id: Int, @Body body: FolderUpdateRequest): FolderDto

    @DELETE("folders/{id}")
    suspend fun deleteFolder(@Path("id") id: Int)

    @GET("todos")
    suspend fun getTodosForFolder(@Query("folder_id") folderId: Int): List<TodoDto>

    @GET("todos")
    suspend fun getRoutineTodos(@Query("view") view: String = "routine"): List<TodoDto>

    @GET("todos/urgent")
    suspend fun getUrgentTodos(): List<TodoDto>

    @POST("todos")
    suspend fun createTodo(@Body body: TodoCreateRequest): TodoDto

    @PATCH("todos/{id}")
    suspend fun updateTodo(@Path("id") id: Int, @Body body: TodoUpdateRequest): TodoDto

    @DELETE("todos/{id}")
    suspend fun deleteTodo(@Path("id") id: Int)

    @POST("todos/{id}/complete")
    suspend fun completeTodo(@Path("id") id: Int): TodoDto

    @POST("todos/{id}/uncomplete")
    suspend fun uncompleteTodo(@Path("id") id: Int): TodoDto

    @POST("voice-todos")
    suspend fun createVoiceTodos(@Body body: VoiceRequest): VoiceResponse
}
