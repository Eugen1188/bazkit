import {
  Injectable
} from '@angular/core';

import {
  HttpClient,
  HttpParams
} from '@angular/common/http';

import {
  Observable
} from 'rxjs';

import {
  CommunityComment,
  CommunityCopyResponse,
  CommunityLikeResponse,
  CommunityPost,
  CommunityPostType,
  CommunityRatingResponse,
  CommunityShareOptions,
  CreateCommunityPostPayload,
  UpdateCommunityPostPayload
} from '../models/community.model';


@Injectable({
  providedIn:
    'root'
})
export class CommunityService {

  private apiUrl =
    this.getApiUrl();


  constructor(
    private http:
      HttpClient
  ) {}


  private getApiUrl():
    string {

    const hostname =
      window.location.hostname;


    const isLocal =
      hostname === 'localhost'
      ||
      hostname === '127.0.0.1';


    if (
      isLocal
    ) {

      return (
        'http://localhost:8000/community/'
      );
    }


    return (
      'http://178.104.47.231:8000/community/'
    );
  }


  getPosts(
    type:
      'all'
      | CommunityPostType =
        'all',

    search:
      string =
        ''
  ): Observable<
    CommunityPost[]
  > {

    let params =
      new HttpParams();


    if (
      type !== 'all'
    ) {

      params =
        params.set(
          'type',
          type
        );
    }


    if (
      search.trim()
    ) {

      params =
        params.set(
          'search',
          search.trim()
        );
    }


    return this.http.get<
      CommunityPost[]
    >(
      `${this.apiUrl}posts/`,
      {
        params
      }
    );
  }


  getPost(
    id:
      number
  ): Observable<
    CommunityPost
  > {

    return this.http.get<
      CommunityPost
    >(
      `${this.apiUrl}posts/${id}/`
    );
  }


  createPost(
    payload:
      CreateCommunityPostPayload
  ): Observable<
    CommunityPost
  > {

    return this.http.post<
      CommunityPost
    >(
      `${this.apiUrl}posts/`,
      payload
    );
  }


  deletePost(
    id:
      number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}posts/${id}/`
    );
  }

  updatePost(
    id: number,
    payload: UpdateCommunityPostPayload
  ): Observable<CommunityPost> {
    return this.http.patch<CommunityPost>(
      `${this.apiUrl}posts/${id}/`,
      payload
    );
  }


  getShareOptions():
    Observable<
      CommunityShareOptions
    > {

    return this.http.get<
      CommunityShareOptions
    >(
      `${this.apiUrl}share-options/`
    );
  }


  getComments(
    postId:
      number
  ): Observable<
    CommunityComment[]
  > {

    return this.http.get<
      CommunityComment[]
    >(
      `${this.apiUrl}posts/${postId}/comments/`
    );
  }


  createComment(
    postId:
      number,

    content:
      string
  ): Observable<
    CommunityComment
  > {

    return this.http.post<
      CommunityComment
    >(
      `${this.apiUrl}posts/${postId}/comments/`,
      {
        content
      }
    );
  }


  deleteComment(
    commentId:
      number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}comments/${commentId}/`
    );
  }


  toggleLike(
    postId:
      number
  ): Observable<
    CommunityLikeResponse
  > {

    return this.http.post<
      CommunityLikeResponse
    >(
      `${this.apiUrl}posts/${postId}/like/`,
      {}
    );
  }


  ratePost(
    postId:
      number,

    value:
      number
  ): Observable<
    CommunityRatingResponse
  > {

    return this.http.post<
      CommunityRatingResponse
    >(
      `${this.apiUrl}posts/${postId}/rating/`,
      {
        value
      }
    );
  }


  copyPost(
    postId:
      number
  ): Observable<
    CommunityCopyResponse
  > {

    return this.http.post<
      CommunityCopyResponse
    >(
      `${this.apiUrl}posts/${postId}/copy/`,
      {}
    );
  }

}
