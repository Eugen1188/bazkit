import {
  CommonModule
} from '@angular/common';

import {
  Component,
  HostListener,
  OnDestroy,
  OnInit
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  Router
} from '@angular/router';

import {
  Subject,
  Subscription,
  debounceTime,
  distinctUntilChanged
} from 'rxjs';

import {
  CommunityPost,
  CommunityPostType,
  CommunityShareOptions,
  CreateCommunityPostPayload
} from '../models/community.model';

import {
  CommunityService
} from '../services/community.service';
import { UiIconComponent } from '../components/ui-icon/ui-icon.component';


@Component({
  selector:
    'app-community',

  standalone:
    true,

  imports: [
    CommonModule,
    FormsModule,
    UiIconComponent
  ],

  templateUrl:
    './community.component.html',

  styleUrl:
    './community.component.scss'
})
export class CommunityComponent
implements OnInit, OnDestroy {

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.isCreateModalOpen) {
      this.closeCreateModal();
    }
  }

  posts:
    CommunityPost[] = [];


  activeFilter:
    'all'
    | CommunityPostType =
      'all';


  searchQuery =
    '';


  isLoading =
    false;

  errorMessage =
    '';


  isCreateModalOpen =
    false;

  createStep:
    'type'
    | 'recipe'
    | 'list'
    | 'thread' =
      'type';


  shareOptions:
    CommunityShareOptions = {

      recipes:
        [],

      saved_lists:
        []
    };


  selectedRecipeId:
    number | null =
      null;

  selectedListId:
    number | null =
      null;


  threadTitle =
    '';

  threadContent =
    '';

  threadCategory =
    'cooking';


  isPublishing =
    false;

  publishError =
    '';


  threadCategories = [

    {
      value:
        'cooking',

      label:
        'Kochen'
    },

    {
      value:
        'shopping',

      label:
        'Einkaufen'
    },

    {
      value:
        'nutrition',

      label:
        'Ernährung'
    },

    {
      value:
        'saving',

      label:
        'Sparen'
    },

    {
      value:
        'products',

      label:
        'Lebensmittel & Produkte'
    },

    {
      value:
        'appliances',

      label:
        'Küchengeräte'
    },

    {
      value:
        'other',

      label:
        'Sonstiges'
    }

  ];


  private searchSubject =
    new Subject<string>();


  private searchSubscription:
    Subscription;


  constructor(
    private communityService:
      CommunityService,

    private router:
      Router
  ) {

    this.searchSubscription =
      this.searchSubject
        .pipe(

          debounceTime(
            350
          ),

          distinctUntilChanged()

        )
        .subscribe(
          () => {

            this.loadPosts();
          }
        );
  }


  ngOnInit():
    void {

    this.loadPosts();
  }


  ngOnDestroy():
    void {

    this.searchSubscription
      .unsubscribe();
  }


  loadPosts():
    void {

    this.isLoading =
      true;

    this.errorMessage =
      '';


    this.communityService
      .getPosts(
        this.activeFilter,
        this.searchQuery
      )
      .subscribe({

        next:
          posts => {

            this.posts =
              posts;

            this.isLoading =
              false;
          },


        error:
          error => {

            console.error(
              'Community konnte nicht geladen werden:',
              error
            );

            this.posts =
              [];

            this.isLoading =
              false;

            this.errorMessage =
              'Die Community konnte nicht geladen werden.';
          }

      });
  }


  onSearchChange(
    value:
      string
  ): void {

    this.searchQuery =
      value;

    this.searchSubject
      .next(
        value
      );
  }


  setFilter(
    filter:
      'all'
      | CommunityPostType
  ): void {

    if (
      this.activeFilter ===
      filter
    ) {

      return;
    }


    this.activeFilter =
      filter;

    this.loadPosts();
  }


  openPost(
    post:
      CommunityPost
  ): void {

    this.router.navigate([
      '/main/community',
      post.id
    ]);
  }


  toggleLike(
    event:
      MouseEvent,

    post:
      CommunityPost
  ): void {

    event.stopPropagation();


    this.communityService
      .toggleLike(
        post.id
      )
      .subscribe({

        next:
          response => {

            post.liked_by_me =
              response.liked;

            post.like_count =
              response.like_count;
          },


        error:
          error => {

            console.error(
              'Like fehlgeschlagen:',
              error
            );
          }

      });
  }


  openCreateModal():
    void {

    this.resetCreateForm();

    this.isCreateModalOpen =
      true;


    this.communityService
      .getShareOptions()
      .subscribe({

        next:
          options => {

            this.shareOptions =
              options;
          },


        error:
          error => {

            console.error(
              'Eigene Inhalte konnten nicht geladen werden:',
              error
            );
          }

      });
  }


  closeCreateModal():
    void {

    if (
      this.isPublishing
    ) {

      return;
    }


    this.isCreateModalOpen =
      false;

    this.resetCreateForm();
  }


  selectCreateType(
    type:
      'recipe'
      | 'list'
      | 'thread'
  ): void {

    this.createStep =
      type;

    this.publishError =
      '';
  }


  backToCreateType():
    void {

    this.createStep =
      'type';

    this.publishError =
      '';
  }


  publishRecipe():
    void {

    if (
      this.selectedRecipeId ===
      null
    ) {

      this.publishError =
        'Bitte wähle ein Rezept aus.';

      return;
    }


    this.publishPost({

      post_type:
        'recipe',

      recipe_id:
        this.selectedRecipeId

    });
  }


  publishList():
    void {

    if (
      this.selectedListId ===
      null
    ) {

      this.publishError =
        'Bitte wähle eine Einkaufsliste aus.';

      return;
    }


    this.publishPost({

      post_type:
        'list',

      saved_list_id:
        this.selectedListId

    });
  }


  publishThread():
    void {

    const title =
      this.threadTitle
        .trim();

    const content =
      this.threadContent
        .trim();


    if (
      !title
    ) {

      this.publishError =
        'Bitte gib einen Titel ein.';

      return;
    }


    if (
      !content
    ) {

      this.publishError =
        'Bitte beschreibe dein Thema.';

      return;
    }


    this.publishPost({

      post_type:
        'thread',

      title,

      content,

      thread_category:
        this.threadCategory

    });
  }


  private publishPost(
    payload:
      CreateCommunityPostPayload
  ): void {

    this.isPublishing =
      true;

    this.publishError =
      '';


    this.communityService
      .createPost(
        payload
      )
      .subscribe({

        next:
          post => {

            this.isPublishing =
              false;

            this.isCreateModalOpen =
              false;

            this.resetCreateForm();


            this.posts = [
              post,
              ...this.posts
            ];
          },


        error:
          error => {

            console.error(
              'Beitrag konnte nicht veröffentlicht werden:',
              error
            );

            this.isPublishing =
              false;


            const response =
              error.error;


            if (
              response?.recipe_id
            ) {

              this.publishError =
                response.recipe_id[0];

              return;
            }


            if (
              response?.saved_list_id
            ) {

              this.publishError =
                response.saved_list_id[0];

              return;
            }


            if (
              response?.title
            ) {

              this.publishError =
                response.title[0];

              return;
            }


            if (
              response?.content
            ) {

              this.publishError =
                response.content[0];

              return;
            }


            this.publishError =
              'Der Beitrag konnte nicht veröffentlicht werden.';
          }

      });
  }


  getPostTypeLabel(
    post:
      CommunityPost
  ): string {

    switch (
      post.post_type
    ) {

      case 'recipe':
        return 'Rezept';

      case 'list':
        return 'Einkaufsliste';

      case 'thread':
        return 'Diskussion';
    }
  }


  getThreadCategoryLabel(
    value:
      string
  ): string {

    return (
      this.threadCategories
        .find(
          item =>
            item.value === value
        )
        ?.label
      ??
      'Diskussion'
    );
  }


  getRelativeTime(
    date:
      string
  ): string {

    const timestamp =
      new Date(
        date
      ).getTime();

    const now =
      Date.now();

    const seconds =
      Math.floor(
        (
          now -
          timestamp
        )
        /
        1000
      );


    if (
      seconds < 60
    ) {

      return 'gerade eben';
    }


    const minutes =
      Math.floor(
        seconds / 60
      );


    if (
      minutes < 60
    ) {

      return (
        `vor ${minutes} Min.`
      );
    }


    const hours =
      Math.floor(
        minutes / 60
      );


    if (
      hours < 24
    ) {

      return (
        `vor ${hours} Std.`
      );
    }


    const days =
      Math.floor(
        hours / 24
      );


    if (
      days < 7
    ) {

      return (
        `vor ${days} Tag${days === 1 ? '' : 'en'}`
      );
    }


    return new Date(
      date
    ).toLocaleDateString(
      'de-DE'
    );
  }


  private resetCreateForm():
    void {

    this.createStep =
      'type';

    this.selectedRecipeId =
      null;

    this.selectedListId =
      null;

    this.threadTitle =
      '';

    this.threadContent =
      '';

    this.threadCategory =
      'cooking';

    this.publishError =
      '';
  }

}
